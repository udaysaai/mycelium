"""
🍄 Mycelium Tutorial 02: Discovering Agents

This tutorial shows you how to:
1. Connect to the Mycelium network
2. Search for agents
3. Send requests to discovered agents

Prerequisites:
    1. Registry running: python -m server.app
    2. At least one agent running (run tutorial 01 first)
"""

"""
🍄 Mycelium Tutorial 02: Discovering Agents
"""

from mycelium import Network

# Connect to the network
network = Network(registry_url="http://localhost:8000")

# List all agents
print("📋 All agents on the network:\n")
network.show_agents()

# Discover weather agents
print("\n🔍 Searching for weather agents...\n")
weather_agents = network.discover("weather forecast temperature")

if weather_agents:
    agent = weather_agents[0]
    print(f"✅ Found: {agent.name} (ID: {agent.agent_id})")
    print(f"📨 Sending request...\n")

    try:
        result = network.request(
            agent_id=agent.agent_id,
            capability="get_weather",
            inputs={"city": "Pune"},
        )
        print(f"✅ Weather Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No weather agents found!")

# Discover translator
print("\n\n🔍 Searching for translator...\n")
translators = network.discover("translate language hindi")

if translators:
    translator = translators[0]
    print(f"✅ Found: {translator.name} (ID: {translator.agent_id})")
    print(f"📨 Sending request...\n")

    try:
        result = network.request(
            agent_id=translator.agent_id,
            capability="translate",
            inputs={"text": "hello", "to": "hindi"},
        )
        print(f"✅ Translation: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No translator agents found!")

# Multi-agent chain — Weather + Translate
print("\n\n🔗 Multi-Agent Chain: Weather → Translate\n")

if weather_agents and translators:
    # Step 1: Get weather from WeatherBuddy
    weather = network.request(
        agent_id=weather_agents[0].agent_id,
        capability="get_weather",
        inputs={"city": "Mumbai"},
    )
    print(f"   Step 1 — Weather: {weather}")

    # Step 2: Translate the condition to Hindi
    weather_text = f"Mumbai weather is {weather.get('temperature')} degrees, {weather.get('condition')}"
    translation = network.request(
        agent_id=translators[0].agent_id,
        capability="translate",
        inputs={"text": weather_text, "to": "hindi"},
    )
    print(f"   Step 2 — Hindi:   {translation}")
    print(f"\n✅ Multi-agent chain complete! Two agents collaborated! 🤝")