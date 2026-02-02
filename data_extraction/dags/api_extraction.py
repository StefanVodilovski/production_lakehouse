import pendulum
import asyncio

from airflow.sdk import dag, task

from api.adzuna.fetch_categories import fetch_categories
from api.adzuna.fetch_jobs import fetch_jobs_by_category
from api.adzuna.process_categories import process_categories


@dag(
    dag_id="adzuna_job_ingestion",
    schedule="@weekly",
    start_date=pendulum.datetime(2026, 1, 1),
    catchup=False,
    tags=["adzuna", "jobs"],
)
def adzuna_dag():

    @task
    def fetch_categories_task():
        return asyncio.run(fetch_categories())

    @task
    def process_categories_task(categories):
        return asyncio.run(process_categories(categories))

    @task
    def fetch_jobs_task(category: str):
        asyncio.run(fetch_jobs_by_category([category]))

    categories = fetch_categories_task()
    category_tags = process_categories_task(categories)

    fetch_jobs_task.expand(category=category_tags)
adzuna_dag()
