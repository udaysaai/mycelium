import requests

BASE_URL = "https://usaai-us-neural-registry.hf.space"

agents = [
    {
        "agent_id": "global_weather_01",
        "name": "CloudWeather",
        "description": "Provides global weather updates via satellite data.",
        "capabilities": [{"name": "get_weather", "description": "Fetch live weather"}],
        "endpoint": "http://localhost:8001"
    },
    {
        "agent_id": "global_crypto_01",
        "name": "BitTracker",
        "description": "Real-time cryptocurrency price monitoring.",
        "capabilities": [{"name": "crypto_price", "description": "Get coin prices"}],
        "endpoint": "http://localhost:8002"
    }
]

print("🍄 Seeding Global Registry...")
for agent in agents:
    res = requests.post(f"{BASE_URL}/api/v1/agents/register", json=agent)
    if res.status_code in [200, 201]:
        print(f"✅ Registered: {agent['name']}")
    else:
        print(f"❌ Failed {agent['name']}: {res.text}")