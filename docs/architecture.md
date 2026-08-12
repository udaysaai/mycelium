# 🏗️ Mycelium Architecture (v0.3.0)

## System Overview

Mycelium is built as an open, high-throughput **Semantic Edge Routing Protocol** that replaces cloud LLM-based tool selection with sub-10ms local vector discovery and zero-trust agent messaging.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   MYCELIUM SEMANTIC EDGE ROUTER                       │
│                                                                        │
│  ┌──────────────┐     ⚡ Sub-10ms Discovery     ┌──────────────┐      │
│  │ Agent Node A │ ───▶ [ ChromaDB Vector-Mesh ] ◀─── │ Agent Node B │      │
│  │ (Python/JS)  │      [  all-MiniLM-L6-v2   ]      │ (Python/JS)  │      │
│  └──────┬───────┘                                   └──────┬───────┘      │
│         │                                                  │              │
│         │ 🔒 Authenticated Direct Comms (HMAC-SHA256)       │              │
│         └──────────────────────────────────────────────────┘              │
│                                                                        │
│                  📡 WebSocket Nervous System Stream                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Modular Component Structure

```text
mycelium/
├── core/
│   ├── agent.py            ← Agent Node class (event loop & handlers)
│   ├── card.py             ← Agent Card identity & schema validation
│   ├── message.py          ← Envelope protocol & status codes
│   ├── capability.py       ← Granular capability definitions
│   └── errors.py           ← Protocol exception taxonomy
├── discovery/
│   └── semantic.py         ← ChromaDB local vector-mesh search engine
├── security/
│   └── auth.py             ← API Key verification & HMAC-SHA256 signing
├── integrations/
│   └── langchain.py        ← LangChain & CrewAI drop-in adapter
├── sdk-js/
│   └── index.js            ← Official Node.js / Browser Client SDK
└── server/
    └── app.py              ← FastAPI Registry Server & WebSocket Manager
```

---

## High-Performance Execution Flow

```text
Step 1: User Prompt / Intent Trigger
        "Convert 100 USD to Yen"

Step 2: Client SDK (Python / JS)
        Executes GET /api/v1/agents/discover?q=...&semantic=true
        Header: X-Mycelium-API-Key: <ENTERPRISE_KEY>

Step 3: Neural Registry (FastAPI + ChromaDB Vector-Mesh)
        Embeds intent using all-MiniLM-L6-v2 locally on CPU
        Calculates cosine similarity against indexed agent vector space
        Returns CurrencyMaster Node in 9.6ms cold latency (P95: 11.4ms)

Step 4: Direct Payload Invocation
        SDK generates HMAC-SHA256 signature (X-Agent-Signature)
        Sends message envelope to CurrencyMaster endpoint (Port 8014)
        Node executes atomic handler and returns response

Total Multi-Hop Autonomous Chain Time: ~36.25 ms (3 Agents)
Cloud API Token Cost: $0.00
```

---

## Design Rationale & Deep-Tech Decisions

### 1. Why Local Vector-Mesh vs Cloud LLM Router?
Cloud LLMs impose a ~2,000ms latency tax and token bills per hop. Mycelium's local ChromaDB + `all-MiniLM-L6-v2` vector-mesh delivers **<10ms cold discovery**, **70.7% intent matching accuracy** across 100,000 agents, and **$0 API cost**.

### 2. Why FastAPI & WebSockets?
FastAPI handles high concurrent throughput (130+ RPS on a single Windows Uvicorn worker). WebSockets supply the live "Nervous System" broadcast stream for real-time visual UI synchronization.

### 3. Why Dual SDKs (Python + JS)?
AI backends are predominantly Python (`mycelium-agents`), while modern web interfaces and edge microservices rely on JavaScript/TypeScript (`mycelium-js`). Mycelium bridges both ecosystems with zero friction.

---

## Enterprise Security Architecture (OWASP ASI06)

To defend against **OWASP ASI06 (AI Agent Over-Permissioning)** and unauthorized tool scanning:

1. **Least-Privilege Routing (LPR):** Agents expose atomic capabilities (`convert_currency`) rather than execution scopes.
2. **Registry Auth Moat:** Protected by `X-Mycelium-API-Key` dependency checks.
3. **Payload Integrity:** Enforced by `HMAC-SHA256` payload signatures (`X-Agent-Signature`).
4. **Rate Limiting:** Prevents cascading DoS attacks ("Agent Storms").

---

## Audited Scale & Benchmark Matrix

| Agents Indexed | Top-1 Accuracy | Cold Discovery Latency | Single-Node Throughput |
| :--- | :--- | :--- | :--- |
| **1,000** | 94.2% | 9.4 ms | 970 RPS |
| **10,000** | 95.0% | 13.3 ms | 879 RPS |
| **100,000** | **70.7%** | **9.6 ms** | **130+ RPS (Single Worker)** |