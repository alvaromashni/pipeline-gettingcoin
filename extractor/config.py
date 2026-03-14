import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.frankfurter.dev/v1")
BASE_CURRENCY = os.getenv("BASE_CURRENCY", "USD")
TARGET_CURRENCIES = os.getenv("TARGET_CURRENCIES", "EUR,BRL,GBP").split(",")
DAYS_BACK = int(os.getenv("DAYS_BACK", 7))

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "datalake"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

def get_date_range():
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=DAYS_BACK - 1)
    return start, end