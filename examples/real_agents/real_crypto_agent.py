"""
💰 REAL Crypto Agent — Uses CoinGecko API (NO API key needed!)
Provides live cryptocurrency prices.
"""

import httpx
from mycelium import Agent

agent = Agent(
    name="CryptoTracker",
    description="Provides REAL live cryptocurrency prices from CoinGecko — Bitcoin, Ethereum, and 10000+ coins",
    version="1.0.0",
    tags=["crypto", "bitcoin", "ethereum", "price", "real", "live", "coingecko", "finance"],
    languages=["english"],
    endpoint="http://localhost:8012",     # ← YEH ADD KAR
)


@agent.on(
    "get_crypto_price",
    description="Get REAL live price of any cryptocurrency in any currency",
    input_schema={
        "coin": "string — coin name (bitcoin, ethereum, dogecoin, etc.)",
        "currency": "string — target currency (usd, inr, eur, etc.)",
    },
    output_schema={
        "coin": "string",
        "price": "number",
        "currency": "string",
        "data_source": "string",
    },
)
def get_crypto_price(coin: str, currency: str = "usd"):
    """Get live crypto price from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin.lower(),
        "vs_currencies": currency.lower(),
        "include_24hr_change": "true",
        "include_market_cap": "true",
        "include_last_updated_at": "true",
    }

    try:
        response = httpx.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            coin_lower = coin.lower()

            if coin_lower in data:
                coin_data = data[coin_lower]
                currency_lower = currency.lower()
                price = coin_data.get(currency_lower, 0)
                change_24h = coin_data.get(f"{currency_lower}_24h_change", 0)
                market_cap = coin_data.get(f"{currency_lower}_market_cap", 0)

                return {
                    "coin": coin,
                    "price": price,
                    "currency": currency.upper(),
                    "change_24h_percent": round(change_24h, 2) if change_24h else 0,
                    "market_cap": market_cap,
                    "trend": "📈 UP" if change_24h and change_24h > 0 else "📉 DOWN",
                    "data_source": "CoinGecko API (LIVE)",
                    "is_real_data": True,
                }
            else:
                return {"error": f"Coin '{coin}' not found. Try: bitcoin, ethereum, dogecoin", "is_real_data": False}
        else:
            return {"error": f"API error: {response.status_code}", "is_real_data": False}

    except Exception as e:
        return {"error": f"Request failed: {str(e)}", "is_real_data": False}


@agent.on(
    "get_top_coins",
    description="Get top 10 cryptocurrencies by market cap",
    input_schema={"currency": "string (default: usd)"},
    output_schema={"coins": "array of coin data"},
)
def get_top_coins(currency: str = "usd"):
    """Get top 10 coins by market cap."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency.lower(),
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1,
    }

    try:
        response = httpx.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            coins = []
            for coin in data:
                coins.append({
                    "rank": coin["market_cap_rank"],
                    "name": coin["name"],
                    "symbol": coin["symbol"].upper(),
                    "price": coin["current_price"],
                    "change_24h": round(coin.get("price_change_percentage_24h", 0) or 0, 2),
                    "market_cap": coin["market_cap"],
                })
            return {
                "coins": coins,
                "currency": currency.upper(),
                "data_source": "CoinGecko API (LIVE)",
                "is_real_data": True,
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
    agent.serve(port=8012)