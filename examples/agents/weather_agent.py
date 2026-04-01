"""
🌤️ Weather Agent — Example Mycelium Agent

This agent provides weather information.
It demonstrates how to:
1. Create an agent
2. Register capabilities
3. Register on the network
4. Serve requests

Run:
    python examples/agents/weather_agent.py
"""

from mycelium import Agent

# Create agent
agent = Agent(
    name="WeatherBuddy",
    description="Provides current weather and forecasts for any city worldwide",
    version="1.0.0",
    author="your@email.com",
    tags=["weather", "forecast", "temperature", "climate"],
    languages=["english", "hindi"],
    endpoint="http://127.0.0.1:8001",  # <--- YE NAYI LINE ADD KAR
)


@agent.on(
    "get_weather",
    description="Get current weather for a city",
    input_schema={"city": "string — city name"},
    output_schema={
        "city": "string",
        "temperature": "number (celsius)",
        "condition": "string",
        "humidity": "number (percentage)",
    },
)
def get_weather(city: str):
    """Get current weather for a city."""
    # In real app, call OpenWeatherMap API
    # For demo, return mock data
    weather_data = {
        "pune": {"temperature": 28, "condition": "Partly Cloudy", "humidity": 65},
        "mumbai": {"temperature": 32, "condition": "Humid", "humidity": 80},
        "delhi": {"temperature": 38, "condition": "Sunny", "humidity": 45},
        "bangalore": {"temperature": 24, "condition": "Rainy", "humidity": 75},
    }

    city_lower = city.lower()
    if city_lower in weather_data:
        data = weather_data[city_lower]
        return {
            "city": city,
            "temperature": data["temperature"],
            "condition": data["condition"],
            "humidity": data["humidity"],
            "unit": "celsius",
        }
    else:
        return {
            "city": city,
            "temperature": 25,
            "condition": "Unknown — city not in database",
            "humidity": 50,
            "unit": "celsius",
        }


@agent.on(
    "get_forecast",
    description="Get 3-day weather forecast for a city",
    input_schema={"city": "string", "days": "integer (1-7)"},
    output_schema={"city": "string", "forecast": "array of daily forecasts"},
)
def get_forecast(city: str, days: int = 3):
    """Get weather forecast."""
    forecast = []
    import random

    conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Thunderstorm"]

    for i in range(min(days, 7)):
        forecast.append(
            {
                "day": i + 1,
                "temperature_high": random.randint(25, 38),
                "temperature_low": random.randint(18, 25),
                "condition": random.choice(conditions),
            }
        )

    return {"city": city, "forecast": forecast, "days": len(forecast)}


if __name__ == "__main__":
    # Show agent info
    agent.info()

    # Register on network
    try:
        agent.register()
    except Exception as e:
        print(f"\n⚠️  Could not register (is the registry running?): {e}")
        print("Starting in standalone mode...\n")

    # Start serving
    agent.serve(host="127.0.0.1", port=8001)