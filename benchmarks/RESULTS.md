# 📊 Mycelium Audited Benchmarks (v0.3.0)

This directory contains the reproducible benchmark suites and official performance reports for the Mycelium Semantic Edge Routing Protocol.

Unlike traditional benchmarks that reward exact ID matches or shared vocabulary, we evaluate Mycelium using **Family-Level Intent Matching** across a massive, highly noisy synthetic corpus of 100,000 agents.

## 🏆 The Benchmark Corpus
- **Total Agents Indexed:** 100,000
- **Storage:** Local ChromaDB Vector-Mesh
- **Embeddings:** `all-MiniLM-L6-v2` (Running 100% locally on CPU)
- **Queries Evaluated:** 441 unique natural language task queries (`benchmarks/data/queries_v2.json`)

---

## 1. Discovery Accuracy vs Latency (Semantic vs Lexical)

Traditional `if/else` logic or BM25 keyword matching fails when user prompts drift. We benchmarked Mycelium's Semantic Discovery against standard BM25 across 100k agents.

| Method | Top-1 Accuracy | Avg Latency (Cold) | P95 Latency |
| :--- | :--- | :--- | :--- |
| **Naive Keyword** | 38.1% | 46.4 ms | 57.6 ms |
| **BM25 Lexical** | 40.4% | 194.0 ms | 247.2 ms |
| **Mycelium (Semantic)** | **70.7%** | **9.6 ms** | **11.4 ms** |

**Key Takeaways:**
*   **Speed:** Semantic discovery runs **20x faster** than BM25 keyword scanning on commodity hardware.
*   **Accuracy:** Achieved a **+30.3% absolute improvement** in intent matching without a single LLM API call.

### 🔬 Evaluation Harness Reconciliation: 70.7% vs. 87.4%

Reviewers comparing reports across different benchmark iterations should note that accuracy reflects evaluation harness design:

| Evaluation Harness | Query Characteristics | BM25 Lexical | Mycelium (Semantic) | Technical Finding |
| :--- | :--- | :--- | :--- | :--- |
| **Harness A (Exact-Match Baseline Dataset)** | Queries share explicit lexical vocabulary with indexed capability descriptors (e.g., query *"crypto coin price"* matching agent *"crypto coin price"*). | 83.4% | **87.4%** | +4.0% delta. Lexical search scores artificially high when queries reuse exact index keywords. |
| **Harness B (v0.3.0 100k Intent Benchmark)** | Realistic natural language task queries with **zero keyword overlap** (e.g., *"should I bring an umbrella"* ➔ Weather, *"how much does dollar cost in rupees"* ➔ Currency). | 40.4% | **70.7%** | **+30.3% delta.** Lexical matching drops sharply when prompts drift; local vector-mesh bridges the vocabulary gap. |

---

## 2. Load & Concurrency (Throughput)

To prove production readiness, the FastAPI registry was subjected to heavy concurrent traffic using an in-memory asynchronous worker simulating real-world B2B SaaS traffic (`benchmarks/results/load_v2.json`).

| Metric | Result | Verdict |
| :--- | :--- | :--- |
| **Concurrent Users** | 100 | High Load |
| **Total Requests** | 9,000 | Sustained Burst |
| **Throughput (RPS)** | ~130.0 req/sec | Capped by Python GIL (Single Worker) |
| **Error Rate** | **0.0%** | Rock Solid Stability 🟢 |
| **Cache Hit Rate** | ~85.9% | In-Memory LRU Cache |

*Note: The ~130 RPS limit is a physical constraint of the Python GIL on a single-core Windows Uvicorn worker. Deploying on Linux with Gunicorn multi-processing linearly scales this throughput.*

---

## 3. Autonomous Workflow Chaining (The LLM Bypass)

Connecting multiple agents typically requires a Cloud LLM (OpenAI) to decide the routing path, imposing a ~2000ms latency tax per hop. We tested a multi-agent autonomous chain (e.g., Weather Agent ➡️ Translator Agent) using Mycelium's native router.

*   **Total Autonomous Chain Latency:** `36.25 ms`
*   **Cloud API Costs:** `$0.00`
*   **Keyword Overlap:** `0%`

### ⏱️ Chain Benchmark Isolation: Routing Overhead vs. Live API Network I/O

- **Protocol Routing & Dispatch Overhead (~36ms):** The 2-hop / 3-hop autonomous chain benchmark (`36.25 ms`) specifically isolates the protocol's computational latency—semantic vector discovery, message envelope serialization, and in-memory relay dispatch—using local mock agent handlers. This guarantees reproducible measurement of the networking layer without third-party network noise.
- **Live Agent Network I/O (~1,000ms – 5,000ms):** When executing real-world chains (such as `scripts/real_world_demo.py` communicating with live public APIs like OpenWeatherMap, CoinGecko, or MyMemory), external network I/O dominates total execution time.
- **LRU Query Caching:** The registry maintains an in-memory LRU query cache (500 entries). Cold semantic vector lookups take ~9.6ms, while warm or repeated intent lookups resolve in **<0.5ms** directly from memory.

---

## 4. Security Architecture & Threat Mitigations

Mycelium aligns with the **OWASP Top 10 for Agentic Applications** by implementing architectural mitigations for **ASI02 (Excessive Agency)** and **ASI03 (Tool Misuse & Privilege Escalation)**:

- **Built-in to Mycelium:**
  - Opt-in `X-Mycelium-API-Key` header gate (`server/app.py`) for private registries.
  - Cryptographic HMAC-SHA256 message signing helper primitives (`security/auth.py`).
  - Sliding-window in-memory `RateLimiter` (`security/auth.py`) to prevent cascading agent call loops.
  - Human-On-The-Loop (HOL) Guard (`security/hol_guard.py`) quarantining mutating operations until human confirmation.
- **Host Coordinator Scope (External):**
  - Fine-grained tiered capability enforcement (T0/T1/T2) and OS execution sandboxing (Docker/gVisor) are handled by the host coordinator (e.g., MAC `policy_engine.py`), outside the network routing layer.

---

## 🔬 How to Reproduce

We believe in 100% transparency. You can reproduce these exact numbers on your local machine using our benchmarking scripts:

**1. Run the Semantic vs BM25 Benchmark:**
```bash
python benchmarks/scripts/run_semantic_benchmark.py
```

**2. Run the High-Concurrency Load Test:**
```bash
python benchmarks/scripts/fix_load_benchmark.py
```

**3. Run the Autonomous Agent Chain Test:**
```bash
python benchmarks/scripts/run_chain_benchmark.py
# Or run the live integration workflow:
python examples/integrations/chain_workflow_demo.py
```

All raw JSON reports are automatically saved in the `reports/` and `results/` directories after execution.
