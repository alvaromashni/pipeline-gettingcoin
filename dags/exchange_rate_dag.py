from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/opt/airflow/extractor")

from extractor import fetch_rates
from loader import load_rates

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def task_extract(**context):
    records = fetch_rates()
    # passa os dados para a proxima task via XCom
    context["ti"].xcom_push(key="records", value=records)

def task_load(**context):
    records = context["ti"].xcom_pull(key="records", task_ids="extract_rates")
    load_rates(records)

with DAG(
    dag_id="exchange_rate_elt",
    description="Extrai cotacoes da Frankfurter API e carrega no PostgreSQL",
    start_date=datetime(2024, 1, 1),
    schedule="0 6 * * *",  # todo dia as 06:00
    catchup=False,
    default_args=default_args,
    tags=["elt", "exchange-rate", "estudos"],
) as dag:

    extract = PythonOperator(
        task_id="extract_rates",
        python_callable=task_extract,
    )

    load = PythonOperator(
        task_id="load_rates",
        python_callable=task_load,
    )

    extract >> load  # define a ordem de execucao