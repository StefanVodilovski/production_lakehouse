from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import config

async_db_engine = create_async_engine(
    config.ASYNC_DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20
)
async_session_factory = async_sessionmaker(async_db_engine, expire_on_commit=False)


@asynccontextmanager
async def get_db_session():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
