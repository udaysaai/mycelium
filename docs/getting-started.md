# 🍄 Getting Started with Mycelium (v0.3.0)

Welcome to **Mycelium**—the Semantic Edge Routing Protocol for Agentic Workflows.

This guide will walk you through setting up the Neural Registry Server, registering specialized agents, and executing sub-10ms semantic discovery in both Python and JavaScript.

---

## 📦 Prerequisites & Installation

- **Python 3.10+** or **Node.js 18+**
- `pip` or `npm`

### Install SDKs

**For Python:**
```bash
pip install mycelium-agents
```

**For JavaScript / TypeScript:**
```bash
npm install mycelium-js
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Boot the Neural Registry Server

The Registry Server acts as the local vector-mesh router powered by FastAPI, ChromaDB, and `all-MiniLM-L6-v2` embeddings.

```bash
python -m server.app
```
*Server starts on `http://127.0.0.1:8000` with live WebSocket stream at `/ws/stream`.*

---

### Step 2: Create & Register an Agent

**Python (`my_agent.py`):**
```python
from mycelium import Agent

agent = Agent(
    name="CurrencyAgent",
    description="Converts currencies using live exchange rates"
)

@agent.on("convert_currency")
def convert_currency(amount: float, from_curr: str, to_curr: str):
    # Business logic or live API call
    rate = 0.92  # USD -> EUR
    return {"converted_amount": amount * rate, "currency": to_curr}

if __name__ == "__main__":
    agent.register(api_key="mycelium_secret_key_2026")
    agent.serve(port=8014)
```

---

### Step 3: Discover & Route Semantically

No hardcoded function names or keyword matching required. Simply query using natural language intent.

**Python Example (`discover.py`):**
```python
from mycelium import NetworkClient

client = NetworkClient(
    registry_url="http://127.0.0.1:8000",
    api_key="mycelium_secret_key_2026"
)

# Semantic Intent Query (Sub-10ms Cold Discovery)
nodes = client.discover("I need to swap 100 dollars into euros", semantic=True)

target = nodes[0]
print(f"✅ Routed to Node: {target.name} (Latency: {target._latency_ms}ms)")

# Execute Agent
result = client.request(
    target.agent_id,
    capability="convert_currency",
    inputs={"amount": 100, "from_curr": "USD", "to_curr": "EUR"}
)
print("Result:", result)
```

**JavaScript / TypeScript Example (`discover.ts`):**
```typescript
import { MyceliumClient } from 'mycelium-js';

const client = new MyceliumClient({
  registryUrl: 'http://127.0.0.1:8000',
  apiKey: 'mycelium_secret_key_2026'
});

async function main() {
  // Discovers Forex/Currency agent with zero keyword overlap in <10ms
  const target = await client.discover("Swap 100 USD into Yen");
  console.log(`✅ Routed Node: ${target.name} | Confidence: ${target._similarity_score * 100}%`);

  const response = await client.request(target.agent_id, "convert_currency", {
    amount: 100,
    from_curr: "USD",
    to_curr: "JPY"
  });
  console.log("Response:", response);
}

main();
```

---

## 🏃 Run Pre-Built Real-World Demos

Boot all 5 real-world agents (Weather, Translator, Crypto, Wikipedia, Currency) and trigger automated workflow chains:

```bash
# Terminal 1: Boot Competition Suite & Real-World Agents
.\start_competition_demo.ps1

# Terminal 2: Trigger Automated 3-Hop Autonomous Chain Demo
python scripts/real_world_demo.py
```

---

## 🔒 Enterprise Security Setup

To enable Enterprise Auth Mode, set the environment variable:

```bash
export MYCELIUM_ENTERPRISE_KEY="your_secure_enterprise_key"
```

All incoming discovery and registration requests will require the `X-Mycelium-API-Key` header, while inter-agent communication will validate `HMAC-SHA256` payload signatures (`X-Agent-Signature`).