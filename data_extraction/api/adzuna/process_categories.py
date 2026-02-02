from sqlalchemy.dialects.postgresql import insert
from config import config, logger
from repostitory.category import insert_categories_batch
from db.engine import get_db_session



async def __extract_category_data(category: dict) -> dict | None:
    tag = category.get("tag")
    label = category.get("label")
    if not tag or not label:
        return None

    return {
        "source": config.ADZUNA_SOURCE_PLACEHOLDER,
        "tag": tag,
        "label": label,
    }

async def process_categories(categories: dict) -> list[str]: 
    logger.info("Processing and storing categories...")
    async with get_db_session() as db:
        results = categories.get("results")
        if not results:
            raise Exception("No categories found")

        payload = []
        tags = []
        for category in results:
            category_data = await __extract_category_data(category)
            if category_data is None:
                logger.warning(f"Invalid category data: {category}")
                continue
            payload.append(category_data)
            tags.append(category_data.get("tag"))
        await insert_categories_batch(db, payload)
        logger.info("Categories processed and stored successfully.")
        return tags