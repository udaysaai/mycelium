# 🍄 Getting Started with Mycelium

## Prerequisites

- Python 3.9+
- pip

## Installation

```bash
pip install mycelium-agents
```

## Your First Agent (2 minutes)

### Step 1: Create an agent

```python
from mycelium import Agent

agent = Agent(
    name="HelloAgent",
    description="A simple greeting agent"
)

@agent.on("greet")
def greet(name: str):
    return {"message": f"Hello, {name}! 🍄"}

if __name__ == "__main__":
    agent.register()
    agent.serve(port=8001)
```

### Step 2: Start the registry

```bash
python -m server.app
```

### Step 3: Start your agent

```bash
python my_agent.py
```

### Step 4: Discover and use it

```python
from mycelium import Network

network = Network()
agents = network.discover("greeting agent")

result = network.request(
    agents[0].agent_id,
    "greet",
    {"name": "World"}
)

print(result)
# → {"message": "Hello, World! 🍄"}
```

## Run the Real-World Demo

```bash
python examples/real_agents/real_weather_agent.py
python examples/real_agents/real_crypto_agent.py
python examples/real_agents/real_translator_agent.py
python examples/real_agents/real_wikipedia_agent.py
python examples/real_agents/real_currency_agent.py

python scripts/real_world_demo.py
```

## Run the Dashboard

```bash
cd antigrav_dashboard
npm install
npm run dev
```

Open: http://localhost:5173

## Next Steps

- Read the [Protocol Spec](protocol-spec.md)
- Explore [Examples](../examples/)
- Check the [API Reference](api-reference.md)
- Read the [FAQ](faq.md)