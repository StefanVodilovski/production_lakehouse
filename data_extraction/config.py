
from logging import Logger
from pydantic_settings import BaseSettings
import os
from airflow.utils.log.logging_mixin import LoggingMixin 


class Config(BaseSettings):
    ADZUNA_SOURCE_PLACEHOLDER: str = os.getenv("ADZUNA_SOURCE_PLACEHOLDER", "ADZUNA")
    ADZUNA_BASE_URL: str = os.getenv("ADZUNA_BASE_URL", "https://api.adzuna.com/v1/api")
    ADZUNA_GB_CATEGORIES_ENDPOIN: str = os.getenv("ADZUNA_CATEGORIES_ENDPOIN", "/jobs/gb/categories")
    ADZUNA_GB_JOBS_ENDPOIN: str = os.getenv("ADZUNA_CATEGORIES_ENDPOIN", "/jobs/gb/search")
    UNKNOWN_JOB_CATEGORY_ID_VALUE: int = 30
    APP_ID:str = os.getenv("APP_ID", "")
    APP_KEY:str = os.getenv("APP_KEY","")
    ASYNC_DATABASE_URL:str = os.getenv("ASYNC_DATABASE_URL","postgresql+asyncpg://postgres:postgres@localhost:5432/transactional_db")



config = Config()
logger = LoggingMixin().log
