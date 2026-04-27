# 🏗️ Mycelium Architecture

## Overview

```
┌─────────────────────────────────────────────────────┐
│                  MYCELIUM NETWORK                   │
│                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌──────────┐  │
│  │ Agent A  │───▶│   REGISTRY   │◀───│ Agent B  │  │
│  │          │    │              │    │          │  │
│  └────┬─────┘    │ • Discovery  │    └────┬─────┘  │
│       │          │ • Semantic   │         │        │
│       │          │ • Trust      │         │        │
│       │          │ • Relay      │         │        │
│       │          └──────────────┘         │        │
│       └────── DIRECT COMMUNICATION ───────┘        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Components

### 1. Python SDK

```
mycelium/
├── core/
│   ├── agent.py        ← Agent class (main)
│   ├── card.py         ← Agent Card (identity)
│   ├── message.py      ← Message protocol
│   ├── capability.py   ← Capability definition
│   └── errors.py       ← Custom exceptions
├── network/
│   └── client.py       ← Network client
├── discovery/
│   └── semantic.py     ← ChromaDB semantic search
├── trust/
│   └── engine.py       ← Trust scoring
├── security/
│   └── auth.py         ← Authentication
└── bridge/
    └── translator.py   ← Cross-domain translation
```

### 2. Registry Server

```
server/
├── app.py              ← FastAPI server
├── routes/
│   ├── agents.py       ← Agent endpoints
│   ├── discovery.py    ← Search endpoints
│   └── messages.py     ← Message relay
└── models/
    └── database.py     ← SQLite persistence
```

### 3. Dashboard

```
antigrav_dashboard/
├── index.html          ← UI structure
├── style.css           ← Glassmorphism styles
└── main.js             ← Logic + API calls
```

---

## Request Flow

```
Step 1: Agent A calls network.discover("weather")
        SDK sends GET /api/v1/agents/discover?q=weather
        Registry runs semantic search
        Returns WeatherAgent

Step 2: Agent A calls network.request(agent_id, "get_weather", inputs)
        SDK sends POST /api/v1/messages/send
        Registry finds Agent B endpoint
        Registry forwards message to Agent B

Step 3: Agent B receives at /mycelium/handle
        Agent B executes get_weather handler
        Agent B returns response

Step 4: Response flows back to Agent A

Total time: ~200-500ms
```

---

## Design Decisions

### Why HTTP and not gRPC?

Simpler, works everywhere, easy to debug. gRPC planned for high-performance use cases later.

### Why centralized registry?

Simpler discovery and trust management. Federation planned for v0.5.

### Why Python first?

90% of AI agents are Python. JS SDK planned for v0.3.

### Why ChromaDB?

Runs locally, free, no API key, good performance.

---

## Ports

| Service | Port |
|---------|------|
| Registry | 8000 |
| Weather Agent | 8010 |
| Translator Agent | 8011 |
| Crypto Agent | 8012 |
| Wikipedia Agent | 8013 |
| Currency Agent | 8014 |
| Dashboard | 5173 |

---

## Scalability Plan

| Phase | Agents | Solution |
|-------|--------|----------|
| Now | ~1,000 | SQLite |
| v0.3 | ~10,000 | PostgreSQL + Redis |
| v0.5 | ~100,000 | Federation |
| v1.0 | 1M+ | Kubernetes |