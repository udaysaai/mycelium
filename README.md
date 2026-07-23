<div align="center">

# 🍄 Mycelium Agents

### The Semantic Networking Protocol for AI Swarms

[![CI State](https://img.shields.io/github/actions/workflow/status/udaysaai/mycelium/codeql.yml?label=CI&style=for-the-badge&color=brightgreen)](https://github.com/udaysaai/mycelium/actions)
[![PyPI Version](https://img.shields.io/pypi/v/mycelium-agents?style=for-the-badge&color=blue)](https://pypi.org/project/mycelium-agents/)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)](https://pypi.org/project/mycelium-agents/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[![Scale](https://img.shields.io/badge/Scale-100k%20Agents-orange?style=for-the-badge)](benchmarks/)
[![Tests](https://img.shields.io/badge/Tests-32%2F32%20Passing-brightgreen?style=for-the-badge)](scripts/system_check.py)
[![Registry](https://img.shields.io/badge/Registry-Online%20(HF)-FFD21E?style=for-the-badge)](https://usaai-us-neural-registry.hf.space)

**[▶ See Live Demo](https://mycelium-agents.netlify.app)** • **[Technical Report](docs/arXiv_draft.md)**

</div>
    
**Stop hardcoding tool selection. Scale your AI product from 5 to 5,000 tools without rewriting your orchestration logic.**

## 📖 The "Tool Routing" Bottleneck
As AI products grow, they transition from single-prompt wrappers to complex multi-tool systems. Developers today rely on hardcoded `if/else` logic, expensive LLM-based routing, or keyword matching that breaks when a user's intent doesn't exactly match a function name.

**Mycelium provides a drop-in semantic discovery layer.** It allows your AI system to dynamically find and route requests to the right internal tool or agent based on meaning, not just exact keywords.

## 📊 Performance Moat (v0.3.0 Benchmark)
We refuse to trade accuracy for speed. In our latest fair-benchmark against traditional Information Retrieval (IR) methods on a corpus of **100,000 agents**:

*   **70.7% Family-Level Top-1 Accuracy** (A +30 percentage point advantage over the strongest lexical baseline, BM25).
*   **<11ms Cold Discovery Latency** (Running 20x faster than BM25 on commodity hardware).
*   **Zero-Cost Local Infrastructure** (Embedding runs locally via `all-MiniLM-L6-v2`; no OpenAI API bills for routing).

*See the full reproduction steps and methodology in our [Benchmarks Ledger](./benchmarks/RESULTS.md).*
---
## 📢 Latest Updates
- **May 2024**: ✅ v0.2.0 Live! Added Semantic Discovery & 100k agent benchmark.
- **May 2024**: 🚀 CrewAI Integration Bridge released. [See Example](link)
- **Next Up**: 🛠️ Authentication Layer & JS SDK (Working on it...)

---

## The Problem

AI agents are everywhere. But they're all **isolated**.

```text
Your Coding Agent ──── cannot talk to ──── Research Agent
Your Email Agent  ──── cannot find   ──── Translation Agent
Your Data Agent   ──── cannot hire   ──── Visualization Agent
```

There are thousands of AI agents being built. **None of them can discover, communicate with, or collaborate with each other.**

It's like having millions of phones with no telephone network.

---

## The Solution

**Mycelium** is the networking protocol that connects AI agents.

```text
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

### 🌐 Deploy a Global Agent in 3 Lines (Zero-Config)
Mycelium automatically handles secure tunneling. No AWS, no Docker, no Port Forwarding.

```python
from mycelium import portal

@portal.share(name="MyGlobalAgent", description="I'm public!")
def handle_task(query: str):
    return f"Processed: {query}"

if __name__ == "__main__":
    handle_task.serve() # Instantly live on the global registry via secure tunnel
```
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

## 📊 Enterprise-Grade Benchmarks (v0.2.0)

Mycelium is stress-tested for production-scale AI swarms. 

**1. Discovery Accuracy at Scale (100,000 Agents)**
Semantic search completely outperforms traditional methods at massive scale.
| Method | Top-1 Accuracy | Avg Latency |
|--------|---------------|-------------|
| Naive Keyword | 75.6% | 136 ms |
| BM25 Lexical | 83.4% | 71 ms |
| **Semantic (Mycelium)**| **87.4%** | **14 ms** |

**2. Network Load & Cache (100 Concurrent Users)**
The built-in Query Cache Layer provides a **20x speedup** under heavy load.
* 10 Users: 970 Requests/sec | 0% error
* 50 Users: 879 Requests/sec | 0% error
* 100 Users: 753 Requests/sec | 0.1% error (p95 = 122ms)

**3. Multi-Agent Workflow Chaining Reliability**
Routing sequential payloads (Agent A → Agent B → Agent C) is flawlessly reliable.
| Chain Depth | Success Rate | Per-Hop Latency |
|-------------|--------------|-----------------|
| 2 Agents | 100.0% | 124.27 ms |
| 3 Agents | 100.0% | 90.04 ms |
| 5 Agents | 100.0% | **83.41 ms** |
*(Note: Per-hop latency decreases as chain depth grows due to dynamic path caching)*

→ [Read the full arXiv Technical Report Draft](docs/arXiv_draft.md)  
→ [Reproduce benchmarks](benchmarks/)

### 🎬 Watch the Demo

https://github.com/user-attachments/assets/2a228337-80f5-479d-8b03-02597ccdc5ef

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

```text
┌────────────────────────────────────────────────────┐
│                  MYCELIUM NETWORK                  │
│                                                    │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐  │
│  │ Agent A  │───▶│   REGISTRY   │◀───│ Agent B │  │
│  │ (Travel) │    │              │    │ (Payment)│  │
│  └────┬─────┘    │ • Discovery  │    └────┬─────┘  │
│       │          │ • Semantic   │         │        │
│       │          │ • Trust      │         │        │
│       │          │ • Relay      │         │        │
│       │          └──────────────┘         │        │
│       │                                   │        │
│       └────── DIRECT COMMUNICATION ───────┘        │
│                                                    │
└────────────────────────────────────────────────────┘

``` 

---

## 🛡️ Security & Reliability (OWASP ASI06 Compliance)

As AI agents move towards autonomy, security risks like **OWASP ASI06 (AI Agent Over-Permissioning)** become critical. Mycelium is engineered to mitigate these risks at the protocol level.

### 🔒 Mitigating AI Agent Over-Permissioning
Mycelium enforces a **Least Privilege Routing (LPR)** model:
- **Granular Capability Mapping**: Agents only register specific atomic capabilities (e.g., `get_weather`), preventing broad system access.
- **Discovery Sandboxing**: The registry only reveals agents that exactly match the semantic intent, preventing unauthorized "agent-to-agent" scanning.
- **Encapsulated Payloads**: All communication is strictly validated via Pydantic schemas, ensuring no malicious execution code is injected into the routing layer.

### 🛠️ Hardened Infrastructure
- **Dependency Guard**: Continuous scanning via CodeQL to prevent supply chain vulnerabilities.
- **Payload Integrity**: (Alpha) Support for signed message envelopes to ensure data hasn't been tampered with during relay.
- **Rate Limiting**: Built-in protection against "Agent Storms" where recursive agent calls could lead to Denial of Service (DoS).


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

```text
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

```text
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
| [Technical Report (arXiv)](docs/arXiv_draft.md) | Official whitepaper draft with full benchmark data |
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
- [x] Enterprise Benchmarks (100k agents scale testing)
- [x] Workflow Chain Benchmarks (100% routing reliability)
- [x] arXiv Technical Report draft completed

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