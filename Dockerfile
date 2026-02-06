FROM apache/airflow:slim-3.1.7rc2-python3.13 AS deps

USER root

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app

COPY data_extraction/pyproject.toml data_extraction/uv.lock ./

RUN uv sync --frozen --no-install-project

FROM apache/airflow:slim-3.1.7rc2-python3.13 

USER root

# Copy virtualenv from build stage
COPY --from=deps /opt/venv /opt/venv

# Give airflow user permission to venv
RUN chown -R airflow: /opt/venv

USER airflow

ENV PYTHONPATH="/opt/venv/lib/python3.13/site-packages:/opt/airflow"

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db

WORKDIR /opt/airflow

COPY data_extraction/dags ./dags
COPY data_extraction/api ./api
COPY data_extraction/db ./db
COPY data_extraction/model ./model
COPY data_extraction/repository ./repository 
COPY data_extraction/config.py ./config.py
COPY data_extraction/alembic.ini ./alembic.ini
COPY data_extraction/mock_data ./mock_data