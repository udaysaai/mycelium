"""
🌤️ REAL Weather Agent — Uses OpenWeatherMap API
Provides ACTUAL live weather data from anywhere in the world.
"""

import os
import httpx
from dotenv import load_dotenv
from mycelium import Agent

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

agent = Agent(
    name="RealWeather",
    description="Provides REAL live weather data from OpenWeatherMap for any city worldwide",
    version="1.0.0",
    tags=["weather", "real", "live", "temperature", "forecast", "openweathermap"],
    languages=["english"],
    endpoint="http://localhost:8010",     # ← YEH ADD KAR
)


@agent.on(
    "get_live_weather",
    description="Get REAL current weather for any city using OpenWeatherMap API",
    input_schema={"city": "string — any city name worldwide"},
    output_schema={
        "city": "string",
        "country": "string",
        "temperature_celsius": "number",
        "feels_like": "number",
        "humidity": "number",
        "condition": "string",
        "wind_speed": "number",
        "data_source": "string",
    },
)
def get_live_weather(city: str):
    """Fetch REAL weather from OpenWeatherMap API."""
    if not API_KEY:
        return {"error": "OpenWeatherMap API key not configured"}

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
    }

    try:
        response = httpx.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature_celsius": round(data["main"]["temp"], 1),
                "feels_like": round(data["main"]["feels_like"], 1),
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
                "pressure": data["main"]["pressure"],
                "visibility": data.get("visibility", "N/A"),
                "data_source": "OpenWeatherMap API (LIVE)",
                "is_real_data": True,
            }
        elif response.status_code == 404:
            return {"error": f"City '{city}' not found", "is_real_data": False}
        else:
            return {"error": f"API error: {response.status_code}", "is_real_data": False}

    except Exception as e:
        return {"error": f"Request failed: {str(e)}", "is_real_data": False}


if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception as e:
        print(f"⚠️ Registry not available: {e}")
    agent.serve(port=8010)