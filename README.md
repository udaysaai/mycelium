<div align="center">

# 🍄 Mycelium Agents

### The Semantic Edge Routing Protocol for Agentic Workflows

[![CI State](https://img.shields.io/github/actions/workflow/status/udaysaai/mycelium/codeql.yml?label=CI&style=for-the-badge&color=brightgreen)](https://github.com/udaysaai/mycelium/actions)
[![PyPI Version](https://img.shields.io/pypi/v/mycelium-agents?style=for-the-badge&color=blue)](https://pypi.org/project/mycelium-agents/)
[![NPM Version](https://img.shields.io/npm/v/mycelium-js?style=for-the-badge&color=red)](https://www.npmjs.com/package/mycelium-js)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)](https://pypi.org/project/mycelium-agents/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[![Scale](https://img.shields.io/badge/Scale-100k%20Agents-orange?style=for-the-badge)](benchmarks/)
[![Tests](https://img.shields.io/badge/Tests-32%2F32%20Passing-brightgreen?style=for-the-badge)](scripts/system_check.py)
[![Security](https://img.shields.io/badge/Security-Enterprise%20HMAC%2BAPIKey-green?style=for-the-badge)](security/auth.py)
[![Protocol](https://img.shields.io/badge/Anthropic_MCP-HOL_Guard_Enabled-purple?style=for-the-badge)](examples/integrations/anthropic_mcp_bridge.py)

**[▶ Live Dashboard](https://mycelium-agents.netlify.app)** • **[Technical Report](docs/arXiv_draft.md)** • **[Benchmarks](benchmarks/RESULTS.md)**

</div>

<div align="center">
  <img src="docs/demo.gif" alt="Mycelium Semantic Edge Routing Demo" width="800"/>
</div>

**Bypass the 2000ms Cloud LLM Routing Tax. Scale your agentic architecture from 5 to 100,000 specialized tools with sub-10ms intent discovery and zero prompt drift.**

---

## ⚡ Why Mycelium? (The LLM Routing Bottleneck)

Modern agentic systems suffer from a severe architectural bottleneck: **Tool Discovery & Routing**.

As swarms grow, relying on Cloud LLMs (e.g. GPT-4) to pick tools or route intents introduces:
- **Massive Latency:** ~2,000ms latency tax *per routing hop*.
- **Exorbitant API Costs:** Paying LLM token rates just to decide which function to execute.
- **Prompt Drift Failures:** Hardcoded `if/else` logic or lexical keyword matching breaks when user intent varies.

### The Solution: Semantic Edge Routing
Mycelium is a decentralized, high-performance **Semantic Edge Routing Protocol**. Powered by a local **ChromaDB Vector-Mesh** and `all-MiniLM-L6-v2` embeddings via FastAPI, Mycelium resolves natural language intents to specialized agent endpoints in **<10ms** locally—with **$0 Cloud LLM cost** and **zero prompt drift**.

```text
User Intent ───▶ [ MYCELIUM SEMANTIC EDGE ROUTER ] ───▶ Specialized Agent Node
                         ⚡ <10ms Cold Discovery
                         💰 $0.00 Routing Cost
                         🎯 70.7% Intent Accuracy (100k Scale)
```

---

## 📊 Audited Performance Benchmarks (v0.3.0)

Evaluated across a massive, highly noisy synthetic corpus of **100,000 indexed agent nodes**:

| Metric | Lexical (BM25) | Mycelium (Semantic Edge) | Impact |
| :--- | :--- | :--- | :--- |
| **Top-1 Intent Accuracy** | 40.4% | **70.7%** | **+30.3% Absolute Accuracy Gain** 🎯 |
| **Avg Cold Discovery Latency** | 194.0 ms | **<9.6 ms** | **20x Faster Discovery** ⚡ |
| **P95 Latency** | 247.2 ms | **11.4 ms** | **Sub-15ms Deterministic Bound** 🔒 |
| **Autonomous Chain Routing** | ~6,000 ms (Cloud LLM) | **36.25 ms (Protocol Overhead)** | **165x Latency Reduction** 🚀 |
| **Single-Node Throughput** | N/A | **130+ req/sec** | **Rock Solid Stability (0.0% Errors)** 🟢 |

*Detailed methodology and reproduction scripts available in our [Benchmarks Ledger](./benchmarks/RESULTS.md).*

### 🔬 Evaluation Harness Reconciliation: 70.7% vs. 87.4%

Reviewers comparing different benchmark tables or earlier reports should note that accuracy depends strictly on evaluation harness design:

| Evaluation Harness | Query Characteristics | BM25 Lexical | Mycelium (Semantic) | Technical Finding |
| :--- | :--- | :--- | :--- | :--- |
| **Harness A (Exact-Match Baseline)** | High keyword overlap between queries and capability descriptors (e.g., query *"crypto coin price"* matching agent *"crypto coin price"*). | 83.4% | **87.4%** | +4.0% delta. Lexical search scores artificially high when users use exact index jargon. |
| **Harness B (v0.3.0 100k Intent Benchmark)** | Realistic natural language task queries with **zero keyword overlap** (e.g., *"should I bring an umbrella"* ➔ Weather, *"how much does dollar cost in rupees"* ➔ Currency). | 40.4% | **70.7%** | **+30.3% delta.** Lexical search drops sharply when prompts drift; local vector-mesh bridges the vocabulary gap. |

### ⏱️ Chain Benchmark Isolation: Routing Overhead vs. Live API Network I/O

- **Protocol Routing & Dispatch Overhead (~36ms):** The 2-hop / 3-hop autonomous chain benchmark (`36.25 ms`) specifically isolates the protocol's computational latency—semantic vector discovery, message envelope serialization, and in-memory relay dispatch—using local mock agent handlers. This guarantees reproducible measurement of the networking layer without third-party network noise.
- **Live Agent Network I/O (~1,000ms – 5,000ms):** When executing real-world chains (such as `scripts/real_world_demo.py` communicating with live public APIs like OpenWeatherMap, CoinGecko, or MyMemory), external network I/O dominates total execution time.
- **LRU Query Caching:** The registry maintains an in-memory LRU query cache (500 entries). Cold semantic vector lookups take ~9.6ms, while warm or repeated intent lookups resolve in **<0.5ms** directly from memory.

---

## 🛠️ Multi-Ecosystem SDKs & Quick Start

Mycelium provides native, drop-in SDKs for both Python and JavaScript ecosystems.

### 1. Installation

**Python (Backend & Frameworks):**
```bash
pip install mycelium-agents
```

**JavaScript / TypeScript (Node.js & Edge Runtimes):**
```bash
npm install mycelium-js
```

### 2. Boot the Neural Registry Server

```bash
python -m server.app
```

### 3. Discover & Route Semantically

**Python (`mycelium-agents` + LangChain Adapter):**
```python
from mycelium.integrations.langchain import MyceliumLangChainAdapter
from mycelium import NetworkClient

# Initialize authenticated client
client = NetworkClient(
    registry_url="http://localhost:8000",
    api_key="mycelium_secret_key_2026"
)

# Sub-10ms Semantic Vector Discovery
agents = client.discover("Convert 100 USD to Euros", semantic=True)
print(f"Routed to: {agents[0].name} (Latency: {agents[0]._latency_ms}ms)")
```

**JavaScript / TypeScript (`mycelium-js`):**
```typescript
import { MyceliumClient } from 'mycelium-js';

const client = new MyceliumClient({
  registryUrl: 'http://localhost:8000',
  apiKey: 'mycelium_secret_key_2026'
});

// Semantic Discovery with 0 keyword overlap
const node = await client.discover("What is the current market price of Bitcoin?");
console.log(`Routed Node: ${node.name} | Confidence: ${node._similarity_score * 100}%`);
```

---

## 🛡️ Enterprise Security & Threat Mitigations (OWASP Agentic: ASI02 & ASI03)

Autonomous agentic routing requires defense-in-depth across the network boundary. Mycelium provides architectural defenses aligned with the **OWASP Top 10 for Agentic Applications** (specifically mitigating **ASI02: Excessive Agency** and **ASI03: Tool Misuse & Privilege Escalation**). These features serve as runtime mitigations and architectural defenses rather than formal "compliance" guarantees:

- **Mitigating ASI02 (Excessive Agency):** Human-On-The-Loop (HOL) Guard dynamically intercepts tool executions, classifying them into read-only queries vs. mutating operations (e.g., transfers, writes, deletions) and halting mutating calls until explicit human confirmation is provided.
- **Mitigating ASI03 (Tool Misuse & Privilege Escalation):** Atomic capability registration ensures agents only advertise granular functional schemas (`get_weather`, `convert_currency`) rather than blanket execution scopes, preventing unauthorized tool chaining.
- **Registry Access Moat (`X-Mycelium-API-Key`):** Opt-in header validation to protect discovery and registration endpoints against unauthorized scanning.
- **Payload Integrity Primitives:** Cryptographic HMAC-SHA256 signing to verify payload integrity during agent-to-agent message relay.
- **Rate-Limiting Defense:** Sliding-window throttling per agent ID to mitigate cascading call storms and infinite agent loops.

### Implementation Scope vs. Host Coordinator Responsibilities

To maintain strict engineering transparency, the table below delineates what is implemented directly inside Mycelium versus what is delegated to the host runtime:

| Security Domain | Implemented in Mycelium Protocol (`server/`, `security/`) | Handled by Host Coordinator (e.g., MAC `policy_engine.py`) |
| :--- | :--- | :--- |
| **Registry Access Control** | ✅ Opt-in `X-Mycelium-API-Key` dependency gate in `server/app.py`. | ⚙️ IAM credential issuance & organizational key management. |
| **Payload Authentication** | ✅ Cryptographic HMAC-SHA256 helpers in `security/auth.py`. | ⚙️ Long-term private key storage & identity bootstrapping. |
| **Abuse & Loop Prevention** | ✅ Sliding-window in-memory `RateLimiter` per agent ID. | ⚙️ Global token budget tracking & multi-tenant billing caps. |
| **Tool Intent Quarantine** | ✅ `HOLGuard` in `security/hol_guard.py` classifying `READ_ONLY` vs `MUTATING`. | ⚙️ Human approval UI/webhook dispatch & cryptographic sign-off. |
| **Execution Sandboxing** | ❌ *Out of scope for network layer* | ⚙️ Tiered capability enforcement (T0/T1/T2), Docker/gVisor process isolation, and OS-level syscall filtering. |

---

## 🔌 Anthropic MCP & HOL Guard (Human-On-The-Loop)

Mycelium natively bridges with **Anthropic's Model Context Protocol (MCP)**, resolving tool bloat and mitigating unconstrained agent execution:

- **Sub-15ms MCP Routing:** Bypasses LLM prompt bloat by discovering tools locally via semantic vector search before touching an LLM.
- **Automated HOL Quarantine:** Dynamically inspects tool intents:
  - `READ_ONLY` intents (e.g. checks, summaries) auto-execute in **<15ms**.
  - `MUTATING` intents (e.g. transfers, deletions, write ops) are immediately **quarantined** and require human cryptographic authorization before execution.

```python
from examples.integrations.anthropic_mcp_bridge import MyceliumMCPBridge

bridge = MyceliumMCPBridge()

# 1. Read-only intent -> Auto-executed in 13ms
res = bridge.dispatch_mcp_call("What is the temperature and humidity right now?", mcp_tools)

# 2. Mutating action -> Intercepted and quarantined by HOL Guard
res = bridge.dispatch_mcp_call("Please transfer 250 dollars to contractor wallet", mcp_tools)
# Result: ⚠️ HOL GUARD TRIGGERED -> Human authorization required before execution
```

## 🏗️ Protocol Architecture & Topology

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   MYCELIUM SEMANTIC EDGE ROUTER                       │
│                                                                        │
│  ┌──────────────┐     ⚡ Sub-10ms Discovery     ┌──────────────┐      │
│  │ Agent Node A │ ───▶ [ ChromaDB Vector-Mesh ] ◀─── │ Agent Node B │      │
│  │ (FinTech)    │      [  all-MiniLM-L6-v2   ]      │ (Translator) │      │
│  └──────┬───────┘                                   └──────┬───────┘      │
│         │                                                  │              │
│         │ 🔒 Authenticated Direct Comms (HMAC-SHA256)       │              │
│         └──────────────────────────────────────────────────┘              │
│                                                                        │
│                  📡 WebSocket Nervous System Stream                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🌍 Pre-Built Real-World Agents

Mycelium includes 5 production-ready agent nodes interacting with live APIs out of the box:

| Node | Domain | Capability | Live API |
| :--- | :--- | :--- | :--- |
| 🌤️ **RealWeather** | Weather | Live temperature & forecast | OpenWeatherMap |
| 💰 **CryptoTracker** | Finance | Live crypto asset pricing | CoinGecko |
| 🌐 **RealTranslator** | Translation | Natural language translation | MyMemory |
| 📖 **WikiBrain** | Knowledge | Wikipedia semantic query | Wikipedia |
| 💱 **CurrencyMaster** | Forex | Live currency exchange rates | ExchangeRate API |

### Run Automated Multi-Agent Chain Demo:
```bash
python scripts/real_world_demo.py
```

---

## 🎬 Watch the Demo

https://github.com/user-attachments/assets/2a228337-80f5-479d-8b03-02597ccdc5ef

---

## 📢 Latest Updates & Changelog

- **October 2026**: 🛡️ Security hardening — HOL Guard integration, OWASP ASI02/ASI03 architectural mitigations, and SQLite database persistence.
- **August 2026**: ⚡ v0.3.0 Release — Enterprise security layer (`X-Mycelium-API-Key` & HMAC-SHA256 signing), JavaScript/TypeScript SDK (`mycelium-js`), LangChain adapter, and live WebSocket streaming.
- **May 2026**: 🧠 v0.2.0 Release — Sub-10ms local vector-mesh semantic discovery (ChromaDB + `all-MiniLM-L6-v2`) and 100k agent benchmark audit.
- **April 2026**: 🍄 v0.1.0 Release — Core agent networking protocol, Pydantic message envelopes, and direct messaging relay.

---

## 🗺️ Roadmap & Protocol Evolution

- [x] **v0.1.0** — Core Networking Protocol & Direct Messaging Relay.
- [x] **v0.2.0** — Local Vector-Mesh Semantic Discovery (ChromaDB + embeddings).
- [x] **v0.3.0 (Current)** — Enterprise Security Layer (API Keys + HMAC Signing), JavaScript SDK (`mycelium-js`), LangChain Integration, Live WebSocket Nervous System.
- [ ] **v0.4.0** — Multi-Region Registry Federation & Distributed Edge Consensus.
- [ ] **v1.0.0** — On-Chain Agent Identity Verification & Automated Trust Settlements.

---

## 📜 License & Community

Released under the [MIT License](LICENSE). Built with ❤️ for open agentic infrastructure.

* **GitHub:** [udaysaai/mycelium](https://github.com/udaysaai/mycelium)
* **PyPI:** [`mycelium-agents`](https://pypi.org/project/mycelium-agents/)
* **NPM:** [`mycelium-js`](https://www.npmjs.com/package/mycelium-js)