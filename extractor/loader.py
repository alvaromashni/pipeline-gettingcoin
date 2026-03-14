import psycopg2
from psycopg2.extras import execute_values
from .config import DB_CONFIG

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_table_if_not_exists(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE SCHEMA IF NOT EXISTS raw;

            CREATE TABLE IF NOT EXISTS raw.exchange_rates (
                id            SERIAL PRIMARY KEY,
                date          DATE NOT NULL,
                base_currency VARCHAR(3) NOT NULL,
                target_currency VARCHAR(3) NOT NULL,
                rate          NUMERIC(18, 6) NOT NULL,
                extracted_at  TIMESTAMP DEFAULT NOW(),
                UNIQUE (date, base_currency, target_currency)
            );
        """)
        conn.commit()
        print("[loader] Tabela verificada/criada.")

def load_rates(records: list[dict]):
    if not records:
        print("[loader] Nenhum registro para carregar.")
        return

    conn = get_connection()
    try:
        create_table_if_not_exists(conn)

        rows = [
            (r["date"], r["base_currency"], r["target_currency"], r["rate"])
            for r in records
        ]

        with conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO raw.exchange_rates (date, base_currency, target_currency, rate)
                VALUES %s
                ON CONFLICT (date, base_currency, target_currency) DO NOTHING
            """, rows)
            conn.commit()

        print(f"[loader] {len(rows)} registros inseridos (duplicatas ignoradas).")
    finally:
        conn.close()