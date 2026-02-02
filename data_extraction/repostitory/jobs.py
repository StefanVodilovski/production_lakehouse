from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, select
from config import  logger
from model.adzuna import JobListing
from sqlalchemy.ext.asyncio import AsyncSession

async def insert_job_listings_batch(
    db: AsyncSession,
    jobs: list[dict],
) -> int:
    logger.info("Inserting job listings batch...")
    if not jobs:
        return 0

    stmt = (
        insert(JobListing)
        .values(jobs)
        .on_conflict_do_nothing(
            index_elements=["source", "job_id"]
        )
        .returning(JobListing.job_id)
    )

    result = await db.execute(stmt)
    await db.commit()
    inserted_ids = result.scalars().all()
    inserted_count = len(inserted_ids)
    logger.info("Job listings batch inserted successfully.")
    return inserted_count



