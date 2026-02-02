from datetime import datetime, timezone
from config import config, logger, read_mock_data
from repostitory.category import get_category_id_by_tag
from repostitory.jobs import insert_job_listings_batch
from db.engine import get_db_session
import httpx
from sqlalchemy.ext.asyncio import AsyncSession


async def __form_iso_format(date_str: str) -> datetime | None:
    if date_str:
        res = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    else:
        res = datetime.now(timezone.utc)
        logger.warning("Job has no created_at, using current UTC time")
    return res


async def __extract_new_job_data(db: AsyncSession, data: dict, category_id: int) -> int:
    results = data.get("results", [])
    if not results:
        return 0

    jobs_batch = []

    for job in results:
        try:
            job_created_at = await __form_iso_format(job.get("created"))
            jobs_batch.append(
                {
                    "source": config.ADZUNA_SOURCE_PLACEHOLDER,
                    "job_id": job.get("id"),
                    "minimum_salary": job.get("salary_min"),
                    "maximum_salary": job.get("salary_max"),
                    "job_post_url": job.get("redirect_url"),
                    "location": job.get("location"),
                    "job_title": job.get("title"),
                    "job_created_at": job_created_at,
                    "job_description": job.get("description"),
                    "company": job.get("company"),
                    "category_id": category_id,
                }
            )

        except Exception as e:
            logger.warning(f"Error processing job listing: {e}")

    inserted_jobs = await insert_job_listings_batch(db, jobs_batch)
    return inserted_jobs


def mock_job_response(category_tag: str) -> dict:
    return read_mock_data(f"{category_tag}.json")


async def fetch_data_from_api(
    current_page_url: str,
    params: dict,
    category: str,
    page: int,
    client: httpx.AsyncClient,
):
    response = await client.get(
        current_page_url,
        params=params,
        headers={"accept": "application/json"},
    )
    if response.status_code == 429:
        raise Exception(
            f"Rate limit exceeded when fetching jobs for category {category} on page {page}. message: {response.text}"
        )
    if response.status_code != 200:
        logger.warning(
            f"Failed to fetch jobs for category {category} on page {page}. Status code: {response.status_code}"
        )
        return None
    data = response.json()
    return data


async def __handle_pagination_by_category(
    db: AsyncSession, search_endpoint: str, params: dict, category_id: int
):
    category = params["category"]
    i = 1
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            logger.info(f"Fetching page {i} for category {category}...")
            current_page_url = f"{search_endpoint}/{str(i)}"
            if config.IS_TEST_MODE:
                data = mock_job_response(category)
            else:
                data = await fetch_data_from_api(
                    current_page_url, params, category, i, client
                )
                if data is None:
                    break
            inserted_data = await __extract_new_job_data(db, data, category_id)
            if inserted_data == 0:
                logger.info(
                    f"No new jobs found for category {category} on page {i}. Stopping pagination."
                )
                break
            i += 1


async def fetch_jobs_by_category(categories: list[str]) -> None:
    logger.info("Fetching jobs from Adzuna API...")
    async with get_db_session() as db:
        try:
            search_endpoint = config.ADZUNA_BASE_URL + config.ADZUNA_GB_JOBS_ENDPOIN
            params = {
                "app_id": config.APP_ID,
                "app_key": config.APP_KEY,
                "results_per_page": 100,
            }
            category_id_map = await get_category_id_by_tag(db)
            for category in categories:
                params["category"] = category
                category_id = category_id_map.get(category)
                if category_id is None:
                    logger.warning(
                        f"Category ID not found for tag {category}. Using UNKNOWN_JOB_CATEGORY_ID_VALUE."
                    )
                    category_id = config.UNKNOWN_JOB_CATEGORY_ID_VALUE
                await __handle_pagination_by_category(
                    db, search_endpoint, params, category_id
                )
            logger.info("Jobs fetched successfully.")
        except Exception as e:
            logger.error(f"Error fetching jobs from Adzuna API: {e}")
            raise e
