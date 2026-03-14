import sys
import os
import json
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow")

from extractor import fetch_rates, load_rates

TEMP_FILE = "/tmp/exchange_rates.json"

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def task_extract(**context):
    records = fetch_rates()
    with open(TEMP_FILE, "w") as f:
        json.dump(records, f)
    print(f"[extract] {len(records)} registros salvos em {TEMP_FILE}")

def task_load(**context):
    if not os.path.exists(TEMP_FILE):
        raise FileNotFoundError(f"Arquivo {TEMP_FILE} nao encontrado. Extract falhou?")

    with open(TEMP_FILE, "r") as f:
        records = json.load(f)

    print(f"[load] {len(records)} registros lidos do arquivo temporario")
    load_rates(records)

    os.remove(TEMP_FILE)
    print(f"[load] Arquivo temporario removido")

with DAG(
    dag_id="exchange_rate_elt",
    description="Extrai cotacoes da Frankfurter API e carrega no PostgreSQL",
    start_date=datetime(2024, 1, 1),
    schedule="0 6 * * *",
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

    extract >> load