from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from config import logger
from model.adzuna import JobCategory

from sqlalchemy.ext.asyncio import AsyncSession

async def insert_categories_batch(
    db: AsyncSession,
    categories: list[dict],
) -> None:
    logger.info("Inserting categories batch...")
    stmt = insert(JobCategory).values(categories).on_conflict_do_nothing(
        index_elements=["source", "tag", "label"]
    )

    await db.execute(stmt)
    await db.commit()
    logger.info("Categories batch inserted successfully.")

async def get_category_id_by_tag(
    db: AsyncSession
) -> dict[str, int]:
    logger.info("Fetching category IDs by tag...")
    stmt = select(JobCategory.tag, JobCategory.id)
    rows = await db.execute(stmt)
    category_map = {tag: id for tag, id in rows.all()}
    logger.info("Category IDs fetched successfully.")
    return category_map
