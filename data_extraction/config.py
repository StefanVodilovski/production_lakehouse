import json
from pathlib import Path
from pydantic_settings import BaseSettings
import os
from airflow.utils.log.logging_mixin import LoggingMixin
from dotenv import load_dotenv
import boto3

load_dotenv()


class Config(BaseSettings):
    ADZUNA_SOURCE_PLACEHOLDER: str = os.getenv("ADZUNA_SOURCE_PLACEHOLDER", "ADZUNA")
    ADZUNA_BASE_URL: str = os.getenv("ADZUNA_BASE_URL", "https://api.adzuna.com/v1/api")
    ADZUNA_GB_CATEGORIES_ENDPOIN: str = os.getenv(
        "ADZUNA_CATEGORIES_ENDPOIN", "/jobs/gb/categories"
    )
    ADZUNA_GB_JOBS_ENDPOIN: str = os.getenv(
        "ADZUNA_CATEGORIES_ENDPOIN", "/jobs/gb/search"
    )
    UNKNOWN_JOB_CATEGORY_ID_VALUE: int = 30
    APP_ID: str = os.getenv("APP_ID", "")
    APP_KEY: str = os.getenv("APP_KEY", "")
    ASYNC_DATABASE_URL: str = os.getenv(
        "ASYNC_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@transactional-postgres:5432/transactional_db",
    )
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local")

    # S3
    S3_BUCKET: str = os.getenv("S3_BUCKET", "")
    S3_MOCK_DATA_PREFIX: str = os.getenv("S3_PREFIX", "mock_data")
    AWS_REGION: str = os.getenv("AWS_REGION", "eu-west-1")


config = Config()
logger = LoggingMixin().log


def __read_mock_data_from_s3(file_name: str):
    bucket = config.S3_BUCKET
    key = f"{config.S3_MOCK_DATA_PREFIX}/{file_name}"
    logger.info(f"Reading mock data from s3://{bucket}/{key} ...")

    s3 = boto3.client("s3", region_name=config.AWS_REGION)
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read().decode("utf-8")
        return json.loads(body)
    except Exception as e:
        logger.exception(f"Failed to read s3://{bucket}/{key}: {e}")
        raise e


def __local_mock(file_name: str) -> dict:
    logger.info("Reading mock data from local filesystem...")
    path = Path(f"mock_data/{file_name}")
    logger.info(f"Reading mock data from path: {path}...")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def read_mock_data(file_name: str) -> dict:
    if config.ENVIRONMENT == "local":
        return __local_mock(file_name)
    elif config.ENVIRONMENT == "dev":
        return __read_mock_data_from_s3(file_name)
    else:
        raise ValueError(f"Unsupported environment: {config.ENVIRONMENT}")
