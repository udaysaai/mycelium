# Mycelium: Semantic Routing for Scalable Multi-Agent Discovery

**Author:** Uday Sonawane, US Neural  
**Date:** July 2026  
**Version:** 0.2.0  
**Links:** [GitHub](https://github.com/udaysaai/mycelium) | [PyPI](https://pypi.org/project/mycelium-agents/)

---

## 1. Abstract

The proliferation of autonomous AI agents necessitates scalable protocols for capability-based discovery and communication. We present Mycelium, an open-source semantic routing protocol that enables agents to discover peers via natural-language capability matching. Mycelium embeds agent descriptions using Sentence-BERT (`all-MiniLM-L6-v2`) into a ChromaDB vector index, achieving sub-11ms average discovery latency at a scale of 100,000 registered agents. In a controlled benchmark against BM25 lexical search and naive keyword matching — using 441 unique, non-circular queries evaluated under cold-cache conditions with embedding time included — Mycelium's semantic router achieves 70.7% Top-1 accuracy, outperforming BM25 (40.4%) by +30.3 percentage points while simultaneously delivering 20× lower latency (9.6ms vs. 194ms). All benchmark code, synthetic data, and reproduction scripts are publicly available under the MIT license.

---

## 2. Introduction

Large Language Model (LLM)-powered AI agents are rapidly evolving from isolated monoliths into cooperative networks of specialized services. A translation agent discovers a currency converter; a medical triage system routes to a prescription parser. This shift from single-agent to multi-agent architectures introduces a fundamental infrastructure challenge: **how does an agent discover the right peer at scale?**

Existing approaches fall short:

- **Hardcoded endpoints** require manual configuration and break under churn.
- **DNS-like registries** (Consul, etcd) support exact-match lookups but not fuzzy capability matching.
- **Blockchain-based directories** offer decentralization at the cost of latency and complexity.
- **Framework-internal routing** (LangChain, AutoGen, CrewAI) works within a single orchestrator but not across independent agent systems.

None of these systems address the core need: **natural-language, intent-based agent discovery at scale.**

We introduce **Mycelium** (v0.2.0), a lightweight semantic routing protocol that fills this gap. Our contributions are:

1. **A semantic discovery engine** that routes natural-language queries to agents via dense vector similarity, achieving 70.7% Top-1 accuracy on 441 unique task-oriented queries across 100,000 agents.
2. **A caching layer** that reduces repeated query latency by 20×, from ~11ms (cold) to <1ms (cached).
3. **An open-source, reproducible benchmark suite** comparing semantic, BM25, and keyword retrieval under identical evaluation conditions, with all scripts, data, and results publicly available.

Mycelium does **not** claim to be production-ready or state-of-the-art. It is a research prototype demonstrating that dense semantic retrieval is both faster and more accurate than lexical baselines for the agent discovery problem.

---

## 3. Related Work

**Agent Communication Standards.** FIPA ACL [1] and KQML [2] established early standards for agent messaging but predate the neural embedding era and lack semantic discovery. The Open Agent Architecture [3] introduced broker-mediated service location but relied on exact capability matching.

**Modern Multi-Agent Frameworks.** LangChain [4], AutoGen [5], and CrewAI [6] provide orchestration layers with built-in tool routing. However, their discovery is confined to agents within a single orchestrator process and does not generalize to cross-system scenarios.

**Service Discovery.** Consul, etcd, and DNS-SD support key-value or tag-based service lookup but require exact keyword matches. They cannot resolve "I need to know if it will rain" to a weather agent.

**Dense Retrieval.** Sentence-BERT [7] introduced efficient sentence-level embeddings for semantic similarity tasks. Vector databases (FAISS [8], Pinecone, Qdrant, Weaviate) have scaled dense retrieval to billions of vectors. ChromaDB [9] provides an embedded, zero-configuration vector store suitable for lightweight deployments.

**Positioning.** Mycelium applies dense retrieval — specifically, Sentence-BERT embeddings over ChromaDB's HNSW index — to the agent discovery problem. Unlike general-purpose search, agent discovery requires structured metadata (capabilities, trust scores, languages) alongside semantic matching.

---

## 4. System Design

### 4.1 Architecture

Mycelium follows a hub-and-spoke topology with a central **Registry** and dynamic **Edge Agents**.

```
┌─────────────────────────────────────────────────────┐
│                  MYCELIUM NETWORK                   │
│                                                     │
│  ┌──────────┐    ┌──────────────────┐  ┌──────────┐│
│  │ Agent A  │───▶│     REGISTRY     │◀─│ Agent B  ││
│  │(Client)  │    │                  │  │(Service) ││
│  └──────────┘    │ ┌──────────────┐ │  └──────────┘│
│                  │ │Semantic Index│ │               │
│                  │ │ (ChromaDB)   │ │               │
│  ┌──────────┐    │ └──────────────┘ │  ┌──────────┐│
│  │ Agent C  │───▶│ ┌──────────────┐ │◀─│ Agent D  ││
│  │(Client)  │    │ │ Query Cache  │ │  │(Service) ││
│  └──────────┘    │ └──────────────┘ │  └──────────┘│
│                  └──────────────────┘               │
└─────────────────────────────────────────────────────┘
```

### 4.2 Agent Card

Each agent registers a structured **Agent Card** — a JSON document describing its identity, capabilities, and operational metadata:

```json
{
  "agent_id": "ag_0e0e7a482683",
  "name": "WeatherBuddy",
  "description": "Provides live weather data for any city",
  "capabilities": [
    {
      "name": "get_weather",
      "description": "Get current weather for any city"
    }
  ],
  "tags": ["weather", "live"],
  "languages": ["english", "hindi"],
  "trust_score": 4.8,
  "status": "online"
}
```

### 4.3 Semantic Routing Algorithm

On registration, each agent card is transformed into a rich text representation via `_build_agent_text()`, combining name, description, capabilities, tags, and languages with structured prefixes. This text is then embedded using `all-MiniLM-L6-v2` (384-dimensional vectors) and upserted into a ChromaDB collection configured with HNSW indexing and cosine distance.

At query time:
1. The natural-language query is encoded into the same embedding space.
2. ChromaDB's HNSW index retrieves the top-*k* nearest agents by cosine similarity.
3. Results are optionally filtered by trust score, status, and capability name.
4. A similarity score (1 − cosine distance) is returned for each match.

### 4.4 Query Cache

An in-memory dictionary cache maps `(query, limit)` tuples to result lists. Cache keys are normalized (lowercased, stripped). The cache uses FIFO eviction at a configurable maximum size (default: 500 entries) and is invalidated on agent registration or deregistration. No time-based expiry is applied.

### 4.5 Workflow Chaining

Mycelium supports sequential multi-agent workflows. A `Chain` object defines an ordered pipeline of agent capabilities. The registry resolves each hop via semantic discovery, and messages are forwarded through the chain with accumulated results.

### 4.6 Transport and SDK

All communication uses REST/HTTP with JSON payloads. The Python SDK (`mycelium-agents` on PyPI) provides `MyceliumAgent` and `MyceliumNetwork` classes for registration, discovery, messaging, and capability handling. The protocol is language-agnostic by design.

---

## 5. Experimental Setup

### 5.1 Hardware

All benchmarks were run on a single consumer workstation. Exact hardware specifications are captured in each result JSON via `platform.processor()`, `platform.platform()`, and memory inspection.

### 5.2 Software

| Component | Version |
|-----------|---------|
| Python | 3.14 |
| FastAPI | ≥0.104 |
| ChromaDB | ≥0.4.0 |
| sentence-transformers | ≥2.2.0 |
| all-MiniLM-L6-v2 | Hugging Face |
| rank_bm25 | ≥0.2.2 |

### 5.3 Synthetic Dataset

**Agent corpus.** 100,000 agent cards were generated by `build_synthetic_agents.py` with `random.seed(42)`. Agents are distributed uniformly across 8 domains (weather, finance, translation, knowledge, support, hiring, legal, medical), each with 5 capability templates. Each agent receives a randomly sampled trust score (2.5–5.0), status, and language set.

**Query set (v3).** 441 unique, task-oriented queries were generated by `fix_ground_truth.py` with `random.seed(42)`. Queries are balanced across all 8 domains (~55 per domain). Critically:
- **No circular vocabulary.** Query templates describe user *tasks* ("will it rain in Pune tomorrow so I can plan a picnic") rather than using agent jargon ("get weather forecast").
- **No repetition.** All 441 queries are unique strings.
- **Parametric diversity.** Templates use fillers for cities, names, topics, companies, and roles. Near-duplicate pairs (embedding cosine > 0.85) were identified and eliminated.

**Anti-circularity verification.** An automated check (`fix_query_diversity.py`) confirmed that the average cosine similarity between each query and its target agent's description is 0.198, with a maximum of 0.604. Zero queries exceed the 0.85 echo threshold.

### 5.4 Ground Truth Construction

Ground truth uses **family-level (domain) evaluation**: a retrieved agent is considered correct if its primary domain tag matches the query's expected domain. With 8 domains and ~12,500 agents per domain, this is deliberately lenient for lexical methods that can match domain keywords, making the benchmark *fairer* to BM25 and keyword baselines.

This is more valid than exact-ID matching because:
1. Multiple agents can legitimately satisfy the same task (e.g., any weather agent can answer a weather query).
2. Domain-level evaluation penalizes semantic errors (returning a legal agent for a weather query) while accepting valid alternatives.
3. It avoids the circular ground-truth problem where the embedding model grades its own ranking.

### 5.5 Baselines

All three methods operate on **identical text representations** produced by `build_agent_text()`:

| Method | Index | Query Processing |
|--------|-------|-----------------|
| **Naive Keyword** | None (linear scan) | Tokenize → count overlapping tokens |
| **BM25 (Okapi)** | Inverted index via `rank_bm25` | Tokenize → TF-IDF scoring |
| **Semantic (Mycelium)** | ChromaDB HNSW (cosine) | Encode via all-MiniLM-L6-v2 → ANN search |

### 5.6 Evaluation Protocol

- **All queries evaluated.** Zero skip rate — if a method returns no results, accuracy = 0 for that query.
- **Cold cache.** Server query cache is flushed (or never populated) before each method's run.
- **Embedding in latency.** For semantic search, the per-query latency includes `model.encode()` time, not just the vector search.
- **Top-K = 3.** Accuracy metrics use K=3 (Top-1, Top-3, MRR).

---

## 6. Results

### 6.1 Discovery Accuracy and Latency (100k Agents)

**Table 1.** Fair benchmark v3 — 441 unique queries, 100,000 agents, cold cache, family-level evaluation.

| Method | Top-1 (%) | Top-3 (%) | MRR | Avg Latency (ms) | P95 Latency (ms) |
|--------|-----------|-----------|-----|-------------------|-------------------|
| Naive Keyword | 38.1 | 46.9 | 0.418 | 46 | 57 |
| BM25 Lexical | 40.4 | 43.5 | 0.420 | 194 | 247 |
| **Semantic (Mycelium)** | **70.7** | **70.7** | **0.707** | **9.6** | **11.4** |

**Key observations:**

1. **Semantic dominates both accuracy and latency.** +30.3pp over BM25 on Top-1, and 20× faster (9.6ms vs 194ms). This is a simultaneous Pareto improvement — no accuracy-latency tradeoff.
2. **Lexical methods struggle with task-oriented queries.** Queries like "should my delivery drones fly in Tokyo this afternoon" share zero keywords with weather agent descriptions. BM25's TF-IDF weighting provides minimal lift over naive token overlap (+2.3pp Top-1).
3. **Semantic Top-1 equals Top-3 (70.7%).** This indicates that when semantic search finds the correct domain, the top-ranked result is already correct — there is little benefit from considering ranks 2–3. Misses are clean misses, not near-misses.

### 6.2 Latency Breakdown (Cold Cache)

**Table 2.** Per-component latency decomposition — 100 queries, cold cache, 100k agents indexed.

| Component | Avg (ms) | P50 (ms) | P95 (ms) | Max (ms) |
|-----------|----------|----------|----------|----------|
| Query embedding (`model.encode`) | 9.1 | 9.2 | 12.4 | 24.0 |
| Vector search (ChromaDB HNSW) | 1.8 | 1.7 | 2.4 | 3.1 |
| **Total cold** | **10.9** | **10.8** | **14.8** | **26.0** |

**Embedding dominates cold latency at 83.5%.** The vector search itself (HNSW approximate nearest neighbor) is O(log N) and takes under 2ms even at 100k scale. This means:
- With a warm cache (bypassing embedding + search), latency drops to <1ms.
- GPU-accelerated embedding (not tested) would reduce the cold path proportionally.
- The bottleneck is the Sentence-BERT forward pass, not the vector database.

### 6.3 Cache Impact

| Condition | Avg Latency | Speedup |
|-----------|-------------|---------|
| Cold (embedding + search) | ~11 ms | 1× |
| Warm (cache hit) | ~0.5 ms | **~20×** |

The 20× cache speedup applies to repeated queries and is validated by the distinct cold/warm measurements. For workloads with high query repetition (e.g., popular agent lookups), this translates directly to throughput gains.

---

## 7. Discussion

### 7.1 Why +30pp Over BM25?

The large accuracy gap between semantic (70.7%) and BM25 (40.4%) is not an artifact — it reflects the fundamental limitation of lexical matching for intent-based discovery. Our query set deliberately uses **task vocabulary** ("should I bring an umbrella") rather than **index vocabulary** ("weather forecast agent"), which breaks keyword overlap. BM25 cannot bridge this vocabulary gap; dense embeddings can.

This gap is larger than the +4pp reported in v1 benchmarks because:
1. **v1 used circular queries** that shared vocabulary with agent descriptions, artificially boosting lexical methods.
2. **v3 queries are genuine paraphrases** of user intent with no keyword overlap with agent descriptions.
3. **The vocabulary gap IS the point** — semantic routing is valuable precisely when users don't know the right keywords.

### 7.2 BM25 Latency Anomaly

BM25's 194ms average is surprisingly high, exceeding even naive keyword's 46ms. This is because `rank_bm25.BM25Okapi` computes TF-IDF scores across the full 100,000-document corpus for every query (O(N) scoring), whereas naive keyword merely counts token overlaps. At 100k scale, BM25's scoring overhead dominates.

### 7.3 Honest Accuracy Assessment

70.7% Top-1 accuracy is **lower** than the 87.4% previously reported in v1. This is expected and correct:
- v1 used circular ground truth where the embedding model graded itself.
- v1 queries shared vocabulary with agent descriptions (tautological).
- v3's 70.7% reflects genuine cross-vocabulary understanding.

A 70.7% hit rate means that for roughly 3 out of 10 queries, the top result is from the wrong domain. This is a meaningful limitation, discussed further in Section 10.

### 7.4 Centralized Registry

The current architecture uses a single FastAPI server with in-memory state. This is a deliberate simplicity tradeoff — sufficient for prototyping and benchmarking, but a single point of failure in production. State is lost on restart; there is no persistent storage layer in the active code path.

---

## 8. Future Work

1. **Decentralized registry.** Federated registry shards with consistent hashing for fault tolerance and geographic distribution.
2. **Real-world evaluation.** Benchmark against real agent descriptions from LangChain Hub, HuggingFace Spaces, or production deployments.
3. **Alternative embedding models.** Evaluate multilingual models (paraphrase-multilingual-MiniLM-L12-v2), domain-specific fine-tuning, and larger models (e5-large, BGE) for accuracy improvements.
4. **Security integration.** The existing `auth.py` and `trust/engine.py` modules are not yet integrated into the request lifecycle. Production deployment requires agent authentication and payload signing.
5. **Persistent storage.** Replace in-memory agent dict with SQLite/PostgreSQL for crash recovery.

---

## 9. Limitations

We acknowledge the following limitations:

1. **Synthetic-only evaluation.** All 100,000 agents and 441 queries are synthetically generated from templates. Real-world agent descriptions are more heterogeneous, and real user queries are less structured. The `benchmarks/data/real/` directory is empty.
2. **Single embedding model.** Results are specific to `all-MiniLM-L6-v2` (384-dim, English-optimized). Performance with multilingual or domain-specific models is unknown.
3. **No peer comparison.** We compare against Naive Keyword and BM25 — deliberately weak baselines. We do not compare against Elasticsearch, FAISS, Qdrant, Weaviate, or other vector databases, nor against any other agent discovery system.
4. **Single-node architecture.** All benchmarks run on a single machine. Network latency, multi-node coordination, and horizontal scaling are not evaluated.
5. **Family-level evaluation.** Ground truth matches at the domain level (~12,500 correct agents per domain). Per-capability or per-agent ground truth would be more discriminating but requires non-circular construction methods not yet implemented.
6. **No statistical significance testing.** Results are from a single benchmark run. Multi-trial runs with bootstrap confidence intervals are planned but not yet completed.

---

## 10. Threats to Validity

| Threat | Severity | Status |
|--------|----------|--------|
| **Cache confound**: reported latency mixed cold/warm queries | 🔴 HIGH | ✅ **RESOLVED** — v3 reports cold-only latency; warm measured separately |
| **Embedding time excluded**: latency didn't include `model.encode()` | 🔴 HIGH | ✅ **RESOLVED** — v3 includes embedding in all latency measurements; breakdown shows 83.5% embedding share |
| **Query repetition**: 40 unique queries repeated 125× each | 🔴 HIGH | ✅ **RESOLVED** — v3 uses 441 unique queries, zero repetition, verified by pairwise similarity check |
| **Circular ground truth**: embedding model graded its own retrieval | 🔴 CRITICAL | ✅ **RESOLVED** — v3 uses domain-tag matching (not embedding similarity) for ground truth; anti-circularity verified (avg cosine 0.198 between query and target description) |
| **Tautological vocabulary**: queries shared keywords with agent descriptions | 🔴 CRITICAL | ✅ **RESOLVED** — v3 queries describe user *tasks*, not agent *capabilities*; max query-description similarity = 0.604 |
| **Synthetic data only**: no real-world agent descriptions or queries | 🟡 MEDIUM | ⚠️ OPEN — acknowledged in limitations |
| **Weak baselines**: no comparison to Elasticsearch, FAISS, Qdrant | 🟡 MEDIUM | ⚠️ OPEN — acknowledged in limitations |
| **Single run**: no confidence intervals or variance reporting | 🟡 MEDIUM | ⚠️ OPEN — multi-trial protocol defined but not yet executed |
| **Single node**: no network latency or distributed evaluation | 🟢 LOW | ⚠️ OPEN — acceptable for a research prototype |

---

## 11. Reproducibility Statement

All code, data, and results required to reproduce this work are publicly available:

- **Source code:** [github.com/udaysaai/mycelium](https://github.com/udaysaai/mycelium) (MIT License)
- **Agent corpus:** `benchmarks/data/synthetic/agent_cards_100k.json` (100,000 agents, `random.seed(42)`)
- **Query set:** `benchmarks/data/queries_v2.json` (441 unique queries, `random.seed(42)`)
- **Benchmark scripts:**
  - `benchmarks/scripts/rerun_fair_benchmark.py` — Discovery accuracy and latency
  - `benchmarks/scripts/fix_latency_accounting.py` — Latency breakdown
  - `benchmarks/scripts/fix_ground_truth.py` — Query generation
  - `benchmarks/scripts/fix_query_diversity.py` — Anti-circularity verification
- **Raw results:** `benchmarks/results/` — JSON files with per-query data
- **Package:** `pip install mycelium-agents` (PyPI)

All data generation uses fixed random seeds for deterministic output. SHA256 checksums for data files are provided in `reproducibility/checksums.sha256`.

---

## 12. Conclusion

We have presented Mycelium, a semantic routing protocol for multi-agent discovery that achieves 70.7% Top-1 accuracy and 9.6ms average cold-cache latency at a scale of 100,000 agents. In a controlled comparison against BM25 and naive keyword baselines — using 441 unique, non-circular task-oriented queries — semantic routing delivers a simultaneous +30 percentage point accuracy improvement and 20× latency reduction.

The key technical insight is that agent discovery is fundamentally a **cross-vocabulary matching** problem: users describe tasks in natural language while agents describe capabilities in domain jargon. Dense embeddings bridge this gap in ways that lexical methods cannot.

Our latency decomposition shows that embedding computation accounts for 83.5% of cold-query time, while HNSW vector search takes under 2ms even at 100k scale. Combined with an in-memory query cache delivering sub-millisecond warm lookups, the system sustains practical throughput for real-time agent networks.

Mycelium is not production-ready. It is a research prototype with acknowledged limitations: synthetic-only evaluation, a single embedding model, no peer-system comparison, and single-node architecture. We release the complete benchmark suite — including the methodology fixes that reduced our reported accuracy from 87.4% to 70.7% — as a contribution toward honest, reproducible evaluation in the multi-agent systems community.

**A paper with 70.7% accuracy and bulletproof methodology is worth infinitely more than a paper with 87.4% and three methodological flaws.**

---

## References

[1] FIPA. *FIPA ACL Message Structure Specification.* Foundation for Intelligent Physical Agents, 2002.

[2] Finin, T., Labrou, Y., & Mayfield, J. *KQML as an Agent Communication Language.* Software Agents, MIT Press, 1997.

[3] Martin, D. L., Cheyer, A. J., & Moran, D. B. *The Open Agent Architecture: A Framework for Building Distributed Software Systems.* Applied Artificial Intelligence, 1999.

[4] Chase, H. *LangChain: Building applications with LLMs through composability.* GitHub, 2022.

[5] Wu, Q., et al. *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation.* arXiv:2308.08155, 2023.

[6] Moura, J. *CrewAI: Framework for orchestrating role-playing AI agents.* GitHub, 2024.

[7] Reimers, N. & Gurevych, I. *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP, 2019.

[8] Johnson, J., Douze, M., & Jégou, H. *Billion-scale similarity search with GPUs.* IEEE Transactions on Big Data, 2019.

[9] Trychta, A., et al. *ChromaDB: The AI-native open-source embedding database.* GitHub, 2023.

[10] Robertson, S., & Zaragoza, H. *The Probabilistic Relevance Framework: BM25 and Beyond.* Foundations and Trends in Information Retrieval, 2009.

[11] Wang, L., et al. *Text Embeddings by Weakly-Supervised Contrastive Pre-training.* arXiv:2212.03533, 2022.

[12] Malkov, Y. A. & Yashunin, D. A. *Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs.* IEEE TPAMI, 2020.

[13] Karpukhin, V., et al. *Dense Passage Retrieval for Open-Domain Question Answering.* EMNLP, 2020.

[14] Guo, J., et al. *A Deep Look into Neural Ranking Models for Information Retrieval.* Information Processing & Management, 2020.

[15] US Neural. *Mycelium: The networking protocol for AI agents.* GitHub Repository, 2026.
