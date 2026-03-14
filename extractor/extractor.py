import requests
from config import API_BASE_URL, BASE_CURRENCY, TARGET_CURRENCIES, get_date_range

def fetch_rates() -> list[dict]:
    start, end = get_date_range()
    currencies = ",".join(TARGET_CURRENCIES)
    url = f"{API_BASE_URL}/{start}..{end}"

    params = {
        "from": BASE_CURRENCY,
        "to": currencies,
    }

    print(f"[extractor] Buscando dados de {start} até {end}...")
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    # A API retorna: { "rates": { "2024-01-01": { "EUR": 0.91, ... }, ... } }

    records = []
    for date_str, rates in data["rates"].items():
        for currency, rate in rates.items():
            records.append({
                "date": date_str,
                "base_currency": BASE_CURRENCY,
                "target_currency": currency,
                "rate": rate,
            })

    print(f"[extractor] {len(records)} registros extraídos.")
    return records