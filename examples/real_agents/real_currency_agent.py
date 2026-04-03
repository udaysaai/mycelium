"""
💱 REAL Currency Agent — Uses ExchangeRate API
Converts between 150+ currencies with REAL live rates.
"""

import os
import httpx
from dotenv import load_dotenv
from mycelium import Agent

load_dotenv()

API_KEY = os.getenv("EXCHANGERATE_API_KEY")

agent = Agent(
    name="CurrencyMaster",
    description="Converts between 150+ currencies using REAL live exchange rates from ExchangeRate API",
    version="1.0.0",
    tags=["currency", "exchange", "real", "convert", "usd", "inr", "finance", "forex"],
    languages=["english"],
    endpoint="http://localhost:8014",     # ← YEH ADD KAR
)


@agent.on(
    "convert_currency",
    description="Convert amount from one currency to another using REAL live rates",
    input_schema={
        "amount": "number — amount to convert",
        "from_currency": "string — 3-letter currency code (USD, INR, EUR, etc.)",
        "to_currency": "string — 3-letter currency code",
    },
    output_schema={
        "converted_amount": "number",
        "exchange_rate": "number",
        "data_source": "string",
    },
)
def convert_currency(amount: float, from_currency: str, to_currency: str):
    """Convert currency using live exchange rates."""

    # Free API without key
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"

    try:
        response = httpx.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            to_upper = to_currency.upper()

            if to_upper in rates:
                rate = rates[to_upper]
                converted = round(amount * rate, 2)
                return {
                    "original_amount": amount,
                    "from_currency": from_currency.upper(),
                    "to_currency": to_upper,
                    "exchange_rate": round(rate, 6),
                    "converted_amount": converted,
                    "formatted": f"{amount} {from_currency.upper()} = {converted} {to_upper}",
                    "data_source": "ExchangeRate API (LIVE)",
                    "is_real_data": True,
                }
            else:
                return {
                    "error": f"Currency '{to_currency}' not found",
                    "available": list(rates.keys())[:20],
                }
        else:
            return {"error": f"API error: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception as e:
        print(f"⚠️ Registry: {e}")
    agent.serve(port=8014)