import pendulum
import asyncio

from airflow.sdk import dag, task
from api.adzuna.extract import run




@dag(
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["api_data_extract"],
)
def extract_data_from_api():

    @task
    def extract():
        asyncio.run(run())

    extract()


extract_data_from_api()
