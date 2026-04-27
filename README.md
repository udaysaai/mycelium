<div align="center">

# 🍄 Mycelium Agents

### Watch 3 AI agents collaborate live — no glue code, no orchestration

**[▶ See Live Demo](https://mycelium-agents.netlify.app)** • **[Try it now](#-quick-start)**

[![Stars](https://img.shields.io/github/stars/udaysaai/mycelium?style=social)](https://github.com/udaysaai/mycelium)
[![PyPI](https://img.shields.io/badge/PyPI-mycelium--agents-blue)](https://pypi.org/project/mycelium-agents/)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-brightgreen)](https://mycelium-agents.netlify.app)

*Bitcoin price → INR conversion → Hindi translation.*
*3 agents. 3 live APIs. 1.1 seconds. Zero orchestration code.*

</div>

---

## The Problem

AI agents are everywhere. But they're all **isolated**.

```
Your Coding Agent ──── cannot talk to ──── Research Agent
Your Email Agent  ──── cannot find   ──── Translation Agent
Your Data Agent   ──── cannot hire   ──── Visualization Agent
```

There are thousands of AI agents being built. **None of them can discover, communicate with, or collaborate with each other.**

It's like having millions of phones with no telephone network.

---

## The Solution

**Mycelium** is the networking protocol that connects AI agents.

```
Your Agent ←→ [MYCELIUM NETWORK] ←→ Any Agent, Anywhere
```

Any agent can:
- 🔍 **Discover** other agents by natural language
- 📨 **Communicate** using a standard protocol
- 🤝 **Collaborate** in multi-agent chains
- ⭐ **Build trust** through successful interactions

---

## ⚡ Quick Start

### Install

```bash
pip install mycelium-agents
```

### Create an Agent (5 lines)

```python
from mycelium import Agent

agent = Agent(name="MyAgent", description="Does amazing things")

@agent.on("greet")
def handle_greet(name: str):
    return {"message": f"Hello, {name}! 🍄"}

agent.serve()
```

### Discover & Use Agents (4 lines)

```python
from mycelium import Network

network = Network()
agents = network.discover("I need a translator")
result = network.request(agents[0].agent_id, "translate",
                         {"text": "Hello", "to": "hindi"})
# → {"translated": "नमस्ते"}
```

**That's it. Your agent is now part of the global network. 🌍**

---

## 🧠 v0.2.0 — Semantic Search

Agents are now found by **MEANING**, not just keywords.

```python
# Before (v0.1 — keyword only)
network.discover("weather")
# Only finds agents with "weather" in name

# Now (v0.2 — semantic)
network.discover("I need temperature data for my city")
# Automatically finds WeatherAgent ✅

network.discover("Speak Hindi please")
# Automatically finds TranslatorAgent ✅

network.discover("What is the value of digital currency?")
# Automatically finds CryptoAgent ✅
```

Powered by **ChromaDB** + **sentence-transformers**. Runs locally. No API key needed.

---

## 🎨 Spatial Dashboard

A visual control center for your Mycelium network. Built with vanilla JS and glassmorphism design.

### 🌐 Live Demo → [mycelium-agents.netlify.app](https://mycelium-agents.netlify.app)

> Watch AI agents orbit the registry core in real-time. Click any agent to inspect capabilities and send requests.

**Features:**
- 🌌 Floating agent pills orbiting the registry core
- ⛓️ Canvas filament lines showing live connections
- 📊 Real-time network stats (Agents, Latency, Messages)
- 🔍 Natural language agent search (Ctrl+K)
- 📡 Send requests directly from the dashboard
- 🖱️ Right-click context menu on any agent
- 🎯 macOS-style dock controls
- 📋 Real-time network logs panel
- ⛓️ Multi-agent chain builder
- 🌗 Dark / Light theme toggle

### Run Locally

```bash
# Step 1: Start the registry
python -m server.app

# Step 2: Start some agents
python examples/real_agents/real_weather_agent.py
python examples/real_agents/real_crypto_agent.py

# Step 3: Open the dashboard
cd antigrav_dashboard
npm install
npm run dev
```

Open: **http://localhost:5173**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  MYCELIUM NETWORK                   │
│                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐  │
│  │ Agent A  │───▶│   REGISTRY   │◀───│ Agent B  │  │
│  │ (Travel) │    │              │    │ (Payment)│  │
│  └────┬─────┘    │ • Discovery  │    └────┬─────┘  │
│       │          │ • Semantic   │         │        │
│       │          │ • Trust      │         │        │
│       │          │ • Relay      │         │        │
│       │          └──────────────┘         │        │
│       │                                   │        │
│       └────── DIRECT COMMUNICATION ───────┘        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🌍 Real-World Agents (Included)

5 production-ready agents using **live APIs**:

| Agent | Capability | API Used |
|-------|-----------|----------|
| 🌤️ RealWeather | Live weather for any city | OpenWeatherMap |
| 💰 CryptoTracker | Live Bitcoin & crypto prices | CoinGecko (free) |
| 🌍 RealTranslator | Translate to 50+ languages | MyMemory (free) |
| 📖 WikiBrain | Wikipedia knowledge & search | Wikipedia (free) |
| 💱 CurrencyMaster | Live exchange rates (150+) | ExchangeRate API |

### Multi-Agent Chain Demo

```bash
python scripts/real_world_demo.py
```

```
⛓️  CHAIN: Crypto Price Translation
→ CryptoTracker:   Bitcoin = $67,432
→ CurrencyMaster:  $67,432 = ₹56,30,613
→ RealTranslator:  67432.5 अमेरिकी डॉलर = 5630613.75 भारतीय रुपया

✅ 3 agents. 3 live APIs. 1 automated chain. (1122ms)
```

---

## 🧪 System Diagnostics

```bash
python scripts/system_check.py
```

```
✅ Registry Server Health      PASS
✅ Agent Registration          PASS
✅ Natural Language Discovery  PASS
✅ Agent-to-Agent Comms        PASS
✅ Multi-Agent Chains          PASS
✅ Error Handling              PASS
✅ SDK Imports                 PASS

📈 Pass Rate: 32/32 (100%)
🟢 ALL SYSTEMS OPERATIONAL
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | First steps with Mycelium |
| [Protocol Spec](docs/protocol-spec.md) | Full protocol specification |
| [Architecture](docs/architecture.md) | System design & decisions |
| [Knowledge Base](docs/MYCELIUM_COMPLETE_KNOWLEDGE_BASE.txt) | Complete postmortem |
| [API Reference](docs/api-reference.md) | REST API docs |
| [FAQ](docs/faq.md) | Frequently asked questions |

---

## 🎯 Examples

| Example | Description |
|---------|-------------|
| [01 — First Agent](examples/tutorials/01_first_agent.py) | Create your first agent |
| [02 — Discover Agents](examples/tutorials/02_discover_agents.py) | Find and use agents |
| [Weather Agent](examples/real_agents/real_weather_agent.py) | Live weather data |
| [Translator Agent](examples/real_agents/real_translator_agent.py) | 50+ languages |
| [Crypto Agent](examples/real_agents/real_crypto_agent.py) | Live crypto prices |
| [Wikipedia Agent](examples/real_agents/real_wikipedia_agent.py) | Knowledge base |
| [Currency Agent](examples/real_agents/real_currency_agent.py) | Exchange rates |

---

## 🗺️ Roadmap

**v0.1.1 ✅ Done**
- [x] Core protocol
- [x] Python SDK (`pip install mycelium-agents`)
- [x] Registry server (FastAPI)
- [x] Agent discovery (keyword-based)
- [x] Agent-to-agent communication
- [x] 5 real-world agents with live APIs
- [x] Multi-agent chain demo
- [x] Spatial dashboard (live on Netlify)
- [x] 32/32 diagnostic tests passing

**v0.2.0 ✅ Done**
- [x] Semantic search (ChromaDB + sentence-transformers)
- [x] Agents found by MEANING not keywords
- [x] 8/8 semantic tests passing

**v0.3.0 📋 Next**
- [ ] Authentication (HMAC + API keys)
- [ ] CLI tool (`mycelium discover "translator"`)
- [ ] JavaScript/TypeScript SDK
- [ ] WebSocket support
- [ ] Agent Marketplace (web UI)
- [ ] LangChain + CrewAI plugins
- [ ] Docker deployment

**v1.0.0 🏆 2027**
- [ ] Stable protocol specification
- [ ] Multi-language SDKs
- [ ] Hosted registry (SaaS)
- [ ] Enterprise features
- [ ] Protocol governance council

---

## 🤝 Contributing

We love contributions! Mycelium is community-driven.

```bash
git clone https://github.com/udaysaai/mycelium.git
cd mycelium
pip install -e ".[dev,server]"
pytest
python -m server.app
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Good first issues:**
- Add a new example agent
- Improve documentation
- Write more tests
- Add language translations

---

## 📜 License

MIT — use it, build on it, make it yours.

---

<div align="center">

**Built with ❤️ from India 🇮🇳**

*If AI agents are the future, they need a way to find each other.*

[⭐ Star this repo](https://github.com/udaysaai/mycelium) if you believe in open agent infrastructure.

**[🎨 Live Dashboard](https://mycelium-agents.netlify.app) • [📦 PyPI](https://pypi.org/project/mycelium-agents/) • [📖 Docs](docs/)**

</div>