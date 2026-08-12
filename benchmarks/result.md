# 📊 Mycelium Audited Benchmarks (v0.3.0)

This directory contains the reproducible benchmark suites and official performance reports for the Mycelium Semantic Edge Routing Protocol.

Unlike traditional benchmarks that reward exact ID matches, we evaluate Mycelium using **Family-Level Intent Matching** across a massive, highly noisy synthetic corpus.

## 🏆 The Benchmark Corpus
- **Total Agents Indexed:** 100,000
- **Storage:** Local ChromaDB Vector-Mesh
- **Embeddings:** `all-MiniLM-L6-v2` (Running 100% locally on CPU)

---

## 1. Discovery Accuracy vs Latency (Semantic vs Lexical)

Traditional `if/else` logic or BM25 keyword matching fails when user prompts drift. We benchmarked Mycelium's Semantic Discovery against standard BM25 across 100k agents.

| Method | Top-1 Accuracy | Avg Latency (Cold) | P95 Latency |
| :--- | :--- | :--- | :--- |
| **BM25 Lexical** | 40.4% | 194.0 ms | 247.2 ms |
| **Mycelium (Semantic)** | **70.7%** | **9.6 ms** | **11.4 ms** |

**Key Takeaways:**
*   **Speed:** Semantic discovery runs **20x faster** than traditional keyword scanning.
*   **Accuracy:** Achieved a **+30% absolute improvement** in intent matching without a single LLM API call.

---

## 2. Load & Concurrency (Throughput)

To prove production readiness, the FastAPI registry was subjected to heavy concurrent traffic using an in-memory asynchronous worker simulating real-world B2B SaaS traffic.

| Metric | Result | Verdict |
| :--- | :--- | :--- |
| **Concurrent Users** | 100 | High Load |
| **Total Requests** | 9,000 | Sustained Burst |
| **Throughput (RPS)** | ~130.0 req/sec | Capped by Python GIL (Single Worker) |
| **Error Rate** | **0.0%** | Rock Solid Stability 🟢 |

*Note: The ~130 RPS limit is a physical constraint of the Python GIL on a single-core Windows Uvicorn worker. Deploying on Linux with Gunicorn multi-processing linearly scales this throughput.*

---

## 3. Autonomous Workflow Chaining (The LLM Bypass)

Connecting multiple agents typically requires a Cloud LLM (OpenAI) to decide the routing path, imposing a ~2000ms latency tax per hop. We tested a multi-agent autonomous chain (e.g., Weather Agent ➡️ Translator Agent) using Mycelium's native router.

*   **Total Autonomous Chain Latency:** `36.25 ms`
*   **Cloud API Costs:** `$0.00`
*   **Keyword Overlap:** `0%`

---

## 🔬 How to Reproduce

We believe in 100% transparency. You can reproduce these exact numbers on your local machine using our benchmarking scripts:

**1. Run the Semantic vs BM25 Benchmark:**
```bash
python scripts/run_semantic_benchmark.py
```

**2. Run the High-Concurrency Load Test:**
```bash
python scripts/fix_load_benchmark.py
```

**3. Run the Autonomous Agent Chain Test:**
```bash
python scripts/chain_workflow_demo.py
```

All raw JSON reports are automatically saved in the `reports/` and `results/` directories after execution.
