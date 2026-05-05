# 🍄 Mycelium Benchmark Results v1

**Protocol Version:** 0.2.0
**Date:** May 2026
**Environment:** Single node, Windows, Python 3.13
**Reproducible:** Yes — all scripts included

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Semantic Discovery Accuracy (10k agents) | **95.0%** |
| Semantic vs Keyword Improvement | **+31%** |
| Peak Throughput | **970 RPS** |
| p95 Latency (light load) | **13ms** |
| Cache Hit Latency | **2ms** |
| Error Rate (100 concurrent) | **0.1%** |

---

## 1. Discovery Benchmark

### Dataset
- **1k benchmark:** 1,000 agents × 1,000 queries
- **10k benchmark:** 10,000 agents × 5,000 queries
- Agent types: weather, finance, translation, knowledge, support, hiring, legal, medical
- Queries: natural language, domain-diverse

### Results — 1,000 Agents

| Metric | Keyword | Semantic | Delta |
|--------|---------|----------|-------|
| Top-1 Accuracy | 60.3% | **94.2%** | +34.0% ✅ |
| Top-3 Recall | 70.2% | **94.2%** | +24.0% ✅ |
| MRR | 0.666 | **0.942** | +0.276 ✅ |
| Avg Latency | 2.4ms | 9.4ms | +7ms |
| P95 Latency | 3.1ms | 12.2ms | +9ms |

### Results — 10,000 Agents

| Metric | Keyword | Semantic | Delta |
|--------|---------|----------|-------|
| Top-1 Accuracy | 63.9% | **95.0%** | +31.0% ✅ |
| Top-3 Recall | 74.5% | **95.0%** | +20.5% ✅ |
| MRR | 0.684 | **0.950** | +0.266 ✅ |
| Avg Latency | 26.3ms | **13.3ms** | -13ms 🚀 |
| P95 Latency | 41.6ms | **15.9ms** | -26ms 🚀 |

### Key Finding
> **At 10,000 agents, semantic search is 31% more accurate AND 2.6x faster than keyword search.**

Accuracy scales with dataset size:
- 1k agents → 94.2%
- 10k agents → 95.0%

---

## 2. Load Benchmark

### Setup
- Registry: Single Python process (FastAPI + uvicorn)
- Cache: In-memory query cache
- OS: Windows 11
- No Redis, no clustering, no load balancer

### Results

| Scenario | Users | RPS | p50 | p95 | p99 | Errors |
|----------|-------|-----|-----|-----|-----|--------|
| Light | 10 | **970** | 9.6ms | **13.9ms** | 19.7ms | **0.0%** |
| Medium | 50 | **879** | 48.2ms | **64.6ms** | 77.4ms | **0.0%** |
| Heavy | 100 | **753** | 95.5ms | **122.7ms** | 141.2ms | **0.1%** |

### Cache Performance

| Request Type | Latency |
|-------------|---------|
| Cold (first query) | 40ms |
| Cached (repeat query) | **2ms** |
| Speedup | **20x** |

### Key Finding
> **970 requests/second on a single Python process with zero errors at light and medium load.**

---

## 3. Scaling Analysis

| Agents | Accuracy | Avg Latency |
|--------|----------|-------------|
| 1,000 | 94.2% | 9.4ms |
| 10,000 | **95.0%** | 13.3ms |

Accuracy **improves** as corpus grows.
Latency stays **sub-15ms** even at 10k agents.

---

## 4. Reproduce These Results

### Install

```bash
pip install mycelium-agents
pip install sentence-transformers chromadb
```

### Generate Dataset

```bash
# 1k benchmark
python benchmarks/scripts/build_synthetic_agents.py
python benchmarks/scripts/build_synthetic_queries.py

# 10k benchmark (set AGENT_COUNT = 10000 in script)
python benchmarks/scripts/build_synthetic_agents.py
```

### Run Discovery Benchmark

```bash
python benchmarks/scripts/run_semantic_benchmark.py
```

### Run Load Benchmark

```bash
# Terminal 1
python -m server.app

# Terminal 2
python benchmarks/scripts/load_benchmark.py
```

### Results Location

```
benchmarks/results/
├── discovery/
│   ├── keyword_*.json
│   └── semantic_vs_keyword_*.json
└── load/
    └── load_*.json
```

---

## 5. Environment

```
OS:       Windows 11
Python:   3.13
FastAPI:  0.104.1
ChromaDB: 0.4.x
Model:    all-MiniLM-L6-v2
Mycelium: 0.2.0
```

---

## 6. What's Next

- [ ] 100k agent benchmark
- [ ] Workflow chain benchmark
- [ ] Redis persistence layer
- [ ] Multi-node federation test
- [ ] arXiv technical report

---

## 7. Citation

```bibtex
@software{mycelium2026,
  title  = {Mycelium: An Open Networking Protocol for AI Agents},
  author = {Uday Saai},
  year   = {2026},
  url    = {https://github.com/udaysaai/mycelium},
  note   = {Benchmark v1}
}
```

---

*Built with ❤️ from India 🇮🇳 by US Neural*
*[GitHub](https://github.com/udaysaai/mycelium) • [PyPI](https://pypi.org/project/mycelium-agents/)*