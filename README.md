<div align="center">

# 🍄 Mycelium

### The Networking Protocol for AI Agents

*Discover. Communicate. Collaborate.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Protocol](https://img.shields.io/badge/protocol-v0.1.0-green.svg)]()
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-brightgreen)](https://mycelium-agents.netlify.app)
[![PyPI](https://img.shields.io/badge/PyPI-mycelium--agents-blue)](https://pypi.org/project/mycelium-agents/)

[Quick Start](#-quick-start) •
[Dashboard](#-spatial-dashboard) •
[Documentation](#-documentation) •
[Examples](#-examples) •
[Contributing](#-contributing)

---

*Like mycelium networks connect trees in a forest,*
*this protocol connects AI agents across the internet.*

**[🎨 Live Dashboard →](https://mycelium-agents.netlify.app)**

</div>

---

## The Problem

AI agents are everywhere. But they're all **isolated**.
Your Coding Agent ──── cannot talk to ──── Research Agent
Your Email Agent ──── cannot find ──── Translation Agent
Your Data Agent ──── cannot hire ──── Visualization Agent

text


There are thousands of AI agents being built.
**None of them can discover, communicate with, or collaborate with each other.**

It's like having millions of phones with no telephone network.

---

## The Solution

**Mycelium** is the networking protocol that connects AI agents.
Your Agent ←→ [MYCELIUM NETWORK] ←→ Any Agent, Anywhere

text


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
Create an Agent (5 lines)
Python

from mycelium import Agent

agent = Agent(name="MyAgent", description="Does amazing things")

@agent.on("greet")
def handle_greet(name: str):
    return {"message": f"Hello, {name}! 🍄"}

agent.serve()
Discover & Use Agents (4 lines)
Python

from mycelium import Network

network = Network()
agents = network.discover("I need a translator")
result = network.request(agents[0].agent_id, "translate",
                         {"text": "Hello", "to": "hindi"})
# → {"translated": "नमस्ते"}
That's it. Your agent is now part of the global network. 🌍

🎨 Spatial Dashboard
A visual control center for your Mycelium network.
Built with vanilla JS and glassmorphism design.

🌐 Live Demo
mycelium-agents.netlify.app

Watch AI agents orbit the registry core in real-time.
Click any agent to inspect capabilities and send requests.

Features
🌌 Floating agent pills orbiting the registry core
⛓️ Canvas filament lines showing live connections
📊 Real-time network stats (Agents, Latency, Messages)
🔍 Natural language agent search (Ctrl+K)
📡 Send requests directly from the dashboard
🖱️ Right-click context menu on any agent
🎯 macOS-style dock controls
📋 Real-time network logs panel
⛓️ Multi-agent chain builder
🌗 Dark / Light theme toggle
Run Locally
Bash

# Step 1: Start the registry
python -m server.app

# Step 2: Start some agents
python examples/real_agents/real_weather_agent.py
python examples/real_agents/real_crypto_agent.py

# Step 3: Open the dashboard
cd antigrav_dashboard
npm install
npm run dev
Open: http://localhost:5173

🏗️ Architecture
text

┌─────────────────────────────────────────────────────┐
│                  MYCELIUM NETWORK                   │
│                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐  │
│  │ Agent A   │───▶│   REGISTRY   │◀───│ Agent B   │  │
│  │ (Travel)  │    │              │    │ (Payment) │  │
│  └────┬──────┘    │ • Discovery  │    └─────┬─────┘  │
│       │           │ • Matching   │          │        │
│       │           │ • Trust      │          │        │
│       │           │ • Relay      │          │        │
│       │           └──────────────┘          │        │
│       │                                     │        │
│       └────── DIRECT COMMUNICATION ─────────┘        │
│                                                     │
└─────────────────────────────────────────────────────┘
🌍 Real-World Agents (Included)
5 production-ready agents using live APIs:

Agent	Capability	API Used
🌤️ RealWeather	Live weather for any city	OpenWeatherMap
💰 CryptoTracker	Live Bitcoin & crypto prices	CoinGecko (free)
🌍 RealTranslator	Translate to 50+ languages	MyMemory (free)
📖 WikiBrain	Wikipedia knowledge & search	Wikipedia (free)
💱 CurrencyMaster	Live exchange rates (150+)	ExchangeRate API
Multi-Agent Chain Demo
Bash

python scripts/real_world_demo.py
text

⛓️  CHAIN: Crypto Price Translation
→ CryptoTracker:   Bitcoin = $67,432
→ CurrencyMaster:  $67,432 = ₹56,30,613
→ RealTranslator:  67432.5 अमेरिकी डॉलर = 5630613.75 भारतीय रुपया

✅ 3 agents. 3 live APIs. 1 automated chain. (1122ms)
🧪 System Diagnostics
Run the full diagnostic suite:

Bash

python scripts/system_check.py
text

✅ Registry Server Health      PASS
✅ Agent Registration          PASS
✅ Natural Language Discovery  PASS
✅ Agent-to-Agent Comms        PASS
✅ Multi-Agent Chains          PASS
✅ Error Handling              PASS
✅ SDK Imports                 PASS

📈 Pass Rate: 32/32 (100%)
🟢 ALL SYSTEMS OPERATIONAL
📚 Documentation
Document	Description
Getting Started	First steps with Mycelium
Protocol Spec	Full protocol specification
Architecture	System design & decisions
Knowledge Base	Complete postmortem
API Reference	REST API docs
FAQ	Frequently asked questions
🎯 Examples
Tutorials
Example	Description
01 — First Agent	Create your first agent
02 — Discover Agents	Find and use agents
Real-World Agents
Agent	Description
Weather Agent	Live weather data
Translator Agent	50+ languages
Crypto Agent	Live crypto prices
Wikipedia Agent	Knowledge base
Currency Agent	Exchange rates
🗺️ Roadmap
v0.1.1 ✅ Current
 Core protocol
 Python SDK (pip install mycelium-agents)
 Registry server (FastAPI)
 Agent discovery (keyword-based)
 Agent-to-agent communication
 5 real-world agents with live APIs
 Multi-agent chain demo
 Spatial dashboard (live on Netlify)
 32/32 diagnostic tests passing
v0.2.0 🔜 June 2026
 Semantic search (ChromaDB vectors)
 Authentication (HMAC + API keys)
 Rate limiting
 CLI tool (mycelium discover "translator")
 JavaScript/TypeScript SDK
 WebSocket support (real-time)
v0.3.0 📋 August 2026
 Agent Marketplace (web UI)
 Payment layer (agents pay agents)
 LangChain + CrewAI plugins
 Docker deployment
v1.0.0 🏆 2027
 Stable protocol specification
 Multi-language SDKs
 Hosted registry (SaaS)
 Enterprise features
 Protocol governance council
🤝 Contributing
We love contributions! Mycelium is community-driven.

Bash

# Setup dev environment
git clone https://github.com/udaysaai/mycelium.git
cd mycelium
pip install -e ".[dev,server]"

# Run tests
pytest

# Run registry
python -m server.app
See CONTRIBUTING.md for guidelines.

Good first issues:

Add a new example agent
Improve documentation
Write more tests
Add language translations
📜 License
MIT — use it, build on it, make it yours.

<div align="center">
Built with ❤️ from India 🇮🇳

If AI agents are the future, they need a way to find each other.

⭐ Star this repo if you believe in open agent infrastructure.

🎨 Live Dashboard • 📦 PyPI • 📖 Docs

</div> 