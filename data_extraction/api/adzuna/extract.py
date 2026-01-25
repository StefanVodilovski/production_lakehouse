from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, select
from config import config, logger
from model.adzuna import JobCategory, JobListing
from db.engine import get_db_session
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

async def fetch_categories() -> dict:
    logger.info("Fetching categories from Adzuna API...")
    params = {
        "app_id": config.APP_ID,
        "app_key": config.APP_KEY,
    }
    category_url = config.ADZUNA_BASE_URL + config.ADZUNA_GB_CATEGORIES_ENDPOIN
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            category_url,
            params=params,
            headers={"accept": "application/json"},
        )
        if response.status_code ==429:
            raise Exception(f"Rate limit exceeded when fetching categories from Adzuna API. message: {response.text}")
        if response.status_code != 200:
            raise Exception(f"Failed to fetch categories from Adzuna API. Status code: {response.status_code}, message: {response.text}")
    data = response.json()
    logger.info("Categories fetched successfully.")
    return data


async def insert_category_to_db(
    db: AsyncSession,
    tag: str,
    label: str,
) -> None:
    try:
        stmt = (
            insert(JobCategory)
            .values(
                source=config.ADZUNA_SOURCE_PLACEHOLDER,
                tag=tag,
                label=label,
            )
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        logger.warning(f"Error inserting category into DB: {e}")
        raise e
    

async def insert_categories_batch(
    db: AsyncSession,
    categories: list[dict],
) -> None:
    stmt = insert(JobCategory).values(categories).on_conflict_do_nothing( 
        index_elements=["source", "tag"]
    )

    await db.execute(stmt)
    await db.commit()


async def process_categories(categories: dict, db: AsyncSession) -> list[str]:
    logger.info("Processing and storing categories...")
    results = categories.get("results")
    if not results:
        raise Exception("No categories found")

    payload = []
    tags = []
    for category in results:
        tag = category.get("tag")
        label = category.get("label")
        if not tag or not label:
            continue

        tags.append(tag)
        payload.append({
            "source": config.ADZUNA_SOURCE_PLACEHOLDER,
            "tag": tag,
            "label": label,
        })
    await insert_categories_batch(db, payload)
    logger.info("Categories processed and stored successfully.")
    return tags


async def fetch_jobs(categories: list):
    logger.info("Fetching jobs for each category...")
    for category in categories:
        logger.info(f"Fetching jobs for category: {category}")

    logger.info("Job fetching completed.")


async def __insert_job_listing_to_db(db: AsyncSession, job_info: dict, category_tag: str) -> str | None:
    try:
      
        stmt = (
            insert(JobListing)
            .values(
                source=config.ADZUNA_SOURCE_PLACEHOLDER,
                job_id=job_info["job_id"],
                minimum_salary=job_info["minimum_salary"],
                maximum_salary=job_info["maximum_salary"],
                job_post_url=job_info["job_post_url"],
                location=job_info["location"],
                job_title=job_info["job_title"],
                job_created_at=job_info["job_created_at"],
                job_description=job_info["job_description"],
                company=job_info["company"],
                category_id=select(JobCategory.id).where(JobCategory.tag == category_tag).scalar_subquery(),
            ).returning(JobListing.job_id) 
        )

        inserted_job = await db.execute(stmt)
        await db.commit()
        return inserted_job.scalar_one_or_none()
    except Exception as e:
        await db.rollback()  
        logger.error(f"Error inserting job listing into DB: {e}")
        raise e
    
async def insert_job_listings_batch(
    db: AsyncSession,
    jobs: list[dict],
) -> int:
    if not jobs:
        return 0

    stmt = (
        insert(JobListing)
        .values(jobs)
        .on_conflict_do_nothing(
            index_elements=["source", "job_id"]
        )
        .returning(func.count())
    )

    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()


async def __form_iso_format(date_str: str) -> datetime | None:
    if date_str:
        res = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    else:
        res = datetime.now(timezone.utc)
        logger.warning(f"Job has no created_at, using current UTC time")
    return res

async def __get_category_id(db: AsyncSession, category_tag: str) -> int | None:
    stmt = select(JobCategory.id).where(JobCategory.tag == category_tag)
    result = await db.execute(stmt)
    category_id = result.scalar_one_or_none()
    if category_id is None:
        logger.warning(f"Category with tag {category_tag} not found in DB.")
        return config.UNKNOWN_JOB_CATEGORY_ID_VALUE
    return category_id


async def __extract_new_job_data(
    db: AsyncSession,
    data: dict,
    category: str,
) -> int:
    results = data.get("results", [])
    if not results:
        return 0

    jobs_batch = []

    for job in results:
        try:
            job_created_at = await __form_iso_format(job.get("created"))
            category_id = __get_category_id(db, category)
            jobs_batch.append({
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
                "category_id": category_id
            })

        except Exception as e:
            logger.warning(f"Error processing job listing: {e}")

    await insert_job_listings_batch(db, jobs_batch)
    return len(jobs_batch)


async def handle_pagination_by_category(db: AsyncSession, search_endpoint: str, params: dict):
    category = params["category"]
    i = 1
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            logger.info(f"Fetching page {i} for category {category}...")
            current_page_url = f"{search_endpoint}/{str(i)}"
            response = await client.get(
                current_page_url,
                params=params,
                headers={"accept": "application/json"},
            )
            if response.status_code ==429:
                raise Exception(f"Rate limit exceeded when fetching jobs for category {category} on page {i}. message: {response.text}")
            if response.status_code != 200:
                logger.warning(f"Failed to fetch jobs for category {category} on page {i}. Status code: {response.status_code}")
                break
            data = response.json()
            inserted_data =  await __extract_new_job_data(db, data, category)
            if inserted_data == 0:
                logger.info(f"No new jobs found for category {category} on page {i}. Stopping pagination.")
                break
            i+=1


async def fetch_jobs_by_category(categories: list[str], db: AsyncSession):
    logger.info("Fetching jobs from Adzuna API...")
    search_endpoint = config.ADZUNA_BASE_URL + config.ADZUNA_GB_JOBS_ENDPOIN
    params = {
        "app_id": config.APP_ID,
        "app_key": config.APP_KEY,
        "results_per_page": 100
    }
    for category in categories:
        params["category"] = category
        await handle_pagination_by_category(db, search_endpoint, params)
    logger.info("Jobs fetched successfully.")



async def run():
    logger.info("Starting Adzuna data extraction...")
    async with get_db_session() as db:
        try:
            categories = await fetch_categories()
            all_categories = await process_categories(categories, db)
            await fetch_jobs_by_category(all_categories, db)
        except Exception as e:
            logger.error(f"Error during Adzuna data extraction : {e}", e)
            raise e
    logger.info("Adzuna data extraction completed.")