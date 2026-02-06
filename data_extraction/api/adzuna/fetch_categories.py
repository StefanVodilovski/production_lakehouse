import httpx
from config import config, logger, read_mock_data


def mock_categories_response() -> dict:
    logger.info("Returning mock categories response for testing...")
    return read_mock_data("categories.json")


async def fetch_categories() -> dict:
    logger.info("Fetching categories from Adzuna API...")
    params = {
        "app_id": config.APP_ID,
        "app_key": config.APP_KEY,
    }
    category_url = config.ADZUNA_BASE_URL + config.ADZUNA_GB_CATEGORIES_ENDPOIN
    async with httpx.AsyncClient(trust_env=False, timeout=30) as client:
        if config.ENVIRONMENT in ["local", "dev"]:
            return mock_categories_response()
        response = await client.get(
            category_url,
            params=params,
            headers={"accept": "application/json"},
        )
        if response.status_code == 429:
            raise Exception(
                f"Rate limit exceeded when fetching categories from Adzuna API. message: {response.text}"
            )
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch categories from Adzuna API. Status code: {response.status_code}, message: {response.text}"
            )
    data = response.json()
    logger.info("Categories fetched successfully.")
    return data
