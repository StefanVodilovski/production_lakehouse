# Beyond Tutorials: State of the art Data Lakehouse 

Production-ready Data Lakehouse implementation using all of the modern data engineering tools. The project is designed to demonstrate the best practices that can be found in enterprise data engineering projects.

The Project includes Data extraction from public Jobs APIs, orchestraited using Apache Airflow and ingested in to a transactional database (PostgreSQL) to simulate a transactional system. From there CDC will be used with Debezium to capture the changes and stream them to Apache Kafka. The data will be consumed and stored in a Data Lakehouse using Snowflake, Iceberg and DBT.

The project will be deployed using Docker and kuberentes on a AWS EKS cluster, and Aiven will be used for managed Kafka and Snowflake services.

This project is a work in progress and will be updated regularly with new features and improvements. The goal is to provide a comprehensive example of a modern data engineering project that can be used as a reference for other projects. 

![Architecture diagram](docs/architecture_diagram.jpeg)

## Architecture Overview

The system follows an event-driven lakehouse architecture:

- Airflow orchestrates data ingestion from external APIs
- PostgreSQL simulates an operational system
- Debezium captures CDC events from PostgreSQL
- Kafka streams changes downstream
- The lakehouse is built using Snowflake, Iceberg and DBT

## Getting started

### Prerequisites

- Python 3.13
- uv (https://docs.astral.sh/uv/getting-started/installation/)
- Docker and Docker Compose (https://docs.docker.com/get-docker/)
- Free API key from Adzuna (https://www.adzuna.com/)

### Walkthrough

UV is used as a package manager and task runner for this project. 

Do the following to install the dependencies and run the data extraction locally:

1. Clone the repository:
```bash
git clone https://github.com/StefanVodilovski/production_lakehouse.git 
```

2.install the dependencies:
```bash
uv uv sync
```
3. Start the transactional database using Docker Compose:
```bash
docker-compose up -d transactional-postgres
```

To run the Airflow jobs you have 2 options, you can either run them locally or using Docker Compose.

- To run them with local Airflow follow the instructions in the Airflow documentation to install Airflow locally (https://airflow.apache.org/docs/apache-airflow/3.1.7/start.html)

The preffered way would be to use the Docker Compose setup, which includes Airflow and all the necessary services. To start the Airflow jobs using Docker Compose, run the following command:
```bash 
 docker compose up -d --build
```

This will start all of the services defined in the `docker-compose.yml` file, including Airflow, PostgreSQL using the custom image from the Dockerfile. 

Then you should be able to access the Airflow webserver at `http://localhost:8080` and see the DAGs for data extraction, which include tasks for fetching categories, fetching jobs, and processing categories using mock requests.

To get the passsword for the Airflow webserver run the following command :

```bash
docker compose exec airflow-webserver cat /opt/airflow/simple_auth_manager_passwords.json.generated    
```

#### Data Extraction

The data extraction is the first step of the systems funcionality. We extract data from the Adzuna API, which provides job listings and categories. The data extraction is done using asynchronous HTTP requests with the httpx library to ensure efficient and fast data retrieval. The extracted data is then processed and stored in a PostgreSQL database, which simulates a transactional system.

The data extraction is scheduled using Apache Airflow, which allows us to automate the data extraction process and ensure that the data is always up-to-date. The Airflow DAG is defined in the `airflow/dags/` folder, and it includes tasks for fetching categories, fetching jobs, and processing categories.

All of the data extraction logic is located in the `data_extrraction/` folder. 

To run the data extraction locally you need to have the PostgreSQL database running, which can be done using Docker Compose. 

To start the Airflow jobs you can create the Docker image from the Dockerfile, and then run the Airflow scheduler and webserver using Docker Compose.


### Future work

- Implement CDC with Debezium to capture changes from PostgreSQL and stream them to Kafka
- Implement data lakehouse using Snowflake, Iceberg and DBT
- Deploy the system on AWS EKS cluster using Kubernetes
- Use Aiven for managed Kafka and Snowflake services
- Implement monitoring and alerting for the system using tools like Prometheus and Grafana
- Implement data quality checks and testing         