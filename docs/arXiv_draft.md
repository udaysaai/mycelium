# Mycelium: A High-Throughput Semantic Routing Protocol for Multi-Agent Systems

**Author:** Uday (US Neural)  
**Date:** October 2023  
**Links:** [GitHub](https://github.com/udaysaai/mycelium) | [PyPI](https://pypi.org/project/mycelium-agents/)

## Abstract
The rapid proliferation of Autonomous AI agents necessitates a standardized protocol for decentralized discovery and communication. We present Mycelium, an open-source networking protocol designed specifically for intelligent systems. Unlike traditional naive or lexical discovery methods, Mycelium implements a semantic routing engine powered by ChromaDB, capable of routing agent payloads with 87.4% Top-1 accuracy at a scale of 100,000 agents. Through comprehensive benchmarking, we demonstrate that Mycelium's integrated caching layer yields a 20x speedup in discovery queries, sustaining over 750 Requests Per Second (RPS) with a p95 latency of 122ms. Furthermore, our workflow chain analysis shows a 100% routing reliability across complex multi-agent chains, with per-hop latency strictly decreasing due to cache optimization. 

---

## 1. Introduction
With the advent of Large Language Models (LLMs), AI systems are shifting from isolated monoliths to networks of specialized, interacting agents. However, standardizing how these agents discover and communicate with each other remains a challenge. Existing frameworks either rely on hardcoded endpoints or computationally expensive P2P blockchain verifications (e.g., *mycelium-md*). 

We introduce **Mycelium** (v0.2.0), a lightweight, scalable, and semantically-aware HTTP-based protocol. It allows agents to register their capabilities dynamically and discover peers using natural language capability matching, effectively acting as the nervous system for AI swarms.

## 2. System Architecture
Mycelium is built on a central Registry Node and dynamic Edge Agents.
*   **Semantic Router:** Uses `all-MiniLM-L6-v2` embeddings via ChromaDB to map string-based query intentions to agent capabilities.
*   **Query Cache Layer:** An in-memory cache that stores frequent semantic mappings, drastically reducing vector-search overhead.
*   **REST/HTTP Transport:** Standardized JSON payloads over HTTP ensure cross-language compatibility (Python, JS, Go).

## 3. Benchmarking Methodology & Results

### 3.1. Discovery Scaling & Accuracy (100k Agents)
To evaluate the routing engine, we populated the registry with 100,000 synthetically generated agents with distinct capabilities. We compared Mycelium's Semantic approach against Naive Keyword matching and standard BM25 Lexical search.

| Method | Top-1 Accuracy | Avg Latency |
|--------|----------------|-------------|
| Naive Keyword | 75.6% | 136 ms |
| BM25 Lexical | 83.4% | 71 ms |
| **Semantic (Mycelium)** | **87.4%** | **14 ms** |

*Result:* Mycelium's semantic engine outperforms BM25 in both accuracy (+4%) and speed (5x faster) at scale.

### 3.2. Network Load & Cache Performance
Load testing was conducted using asynchronous HTTP clients to simulate concurrent agent requests.

*   **10 Concurrent Users:** 970 RPS | p95 = 13 ms | 0% error
*   **50 Concurrent Users:** 879 RPS | p95 = 64 ms | 0% error
*   **100 Concurrent Users:** 753 RPS | p95 = 122 ms | 0.1% error

*Cache Impact:* Cold cache queries averaged 40ms, while cached queries averaged 2ms—a **20x speedup** critical for high-frequency trading or real-time agent networks.

### 3.3. Multi-Agent Workflow Chaining
We evaluated the protocol overhead when agents execute sequential workflows (e.g., Agent A routes to B, which routes to C). 

| Chain Depth | Success Rate | Total Chain Latency | Avg Per-Hop Latency |
|-------------|--------------|---------------------|---------------------|
| 2 Agents | 100.0% | 248.55 ms | 124.27 ms |
| 3 Agents | 100.0% | 270.11 ms | 90.04 ms |
| 5 Agents | 100.0% | 417.07 ms | **83.41 ms** |

*Result:* The protocol maintains absolute (100%) reliability. Notably, as chain depth increases, the average per-hop latency decreases (down to 83.41ms), proving that the protocol efficiently leverages historical routing paths via caching.

## 4. Conclusion
Mycelium provides a robust, production-ready foundation for multi-agent discovery and routing. By combining lightweight semantic vector search with aggressive query caching, it resolves the bottleneck of agent-to-agent capability matching. Future work will include decentralized registry shards (US Neural 'Probe' integration) and OpenSSF certification for secure agent payload execution.

## 5. References
1. US Neural / Mycelium GitHub Repository (2023).
2. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.