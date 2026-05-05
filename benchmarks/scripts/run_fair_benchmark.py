"""
⚖️ Mycelium Fair Benchmark
Compares:
1. Naive keyword search
2. BM25 lexical search
3. Semantic vector search

Goal:
Make the comparison FAIR at 100k scale.
"""

import json
import re
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi


# ============================================================
# CONFIG
# ============================================================

AGENTS_FILE = "benchmarks/data/synthetic/agent_cards_100k.json"
QUERIES_FILE = "benchmarks/data/synthetic/queries_5k.json"
RESULTS_DIR = "benchmarks/results/discovery"

MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5


# ============================================================
# UTILS
# ============================================================

def save_json(path: str, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def percentile(data: list, p: float) -> float:
    if not data:
        return 0.0
    data = sorted(data)
    idx = int(len(data) * p / 100)
    idx = min(idx, len(data) - 1)
    return round(data[idx], 2)

def tokenize(text: str):
    return re.findall(r"[a-z0-9]+", text.lower())


# ============================================================
# TEXT BUILDING
# ============================================================

def build_agent_text(agent: dict) -> str:
    """
    Build same text for lexical + semantic.
    Keep comparison fair.
    """
    parts = []

    name = agent.get("name", "")
    description = agent.get("description", "")
    tags = agent.get("tags", [])
    languages = agent.get("languages", [])
    capabilities = agent.get("capabilities", [])

    if name:
        parts.append(name)

    if description:
        parts.append(description)

    # capability names + descriptions
    for cap in capabilities:
        cap_name = cap.get("name", "")
        cap_desc = cap.get("description", "")
        if cap_name:
            parts.append(cap_name)
        if cap_desc:
            parts.append(cap_desc)

    # boost tags a bit by repeating once
    if tags:
        parts.extend(tags)
        parts.extend(tags)

    if languages:
        parts.extend(languages)

    return " ".join(parts)


# ============================================================
# DOMAIN MAPPING
# ============================================================

def build_domain_map(agents):
    """
    Domain → relevant agent_ids
    """
    domain_to_agents = defaultdict(list)

    for agent in agents:
        aid = agent["agent_id"]
        text = build_agent_text(agent).lower()
        tags = [t.lower() for t in agent.get("tags", [])]

        for domain in [
            "weather", "finance", "translation", "knowledge",
            "support", "hiring", "legal", "medical"
        ]:
            if domain in text or domain in tags:
                domain_to_agents[domain].append(aid)

        # common synonym mapping
        if "crypto" in text:
            domain_to_agents["finance"].append(aid)
        if "wiki" in text or "fact" in text or "biography" in text:
            domain_to_agents["knowledge"].append(aid)
        if "translate" in text or "language" in text or "hindi" in text:
            domain_to_agents["translation"].append(aid)

    return domain_to_agents


# ============================================================
# SEARCH METHODS
# ============================================================

def naive_keyword_search(query, agents, k=5):
    """
    Old baseline — simple substring overlap
    """
    query_words = set(tokenize(query))
    scored = []

    for agent in agents:
        text = build_agent_text(agent).lower()
        score = 0
        for word in query_words:
            if word in text:
                score += 1
        if score > 0:
            scored.append((score, agent["agent_id"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [aid for _, aid in scored[:k]]


def build_bm25_index(agents):
    """
    BM25 lexical index
    """
    print(f"\n🔨 Building BM25 index for {len(agents)} agents...")
    corpus = [build_agent_text(a) for a in agents]
    tokenized_corpus = [tokenize(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    id_lookup = [a["agent_id"] for a in agents]
    print("✅ BM25 index built")
    return bm25, id_lookup


def bm25_search(query, bm25, id_lookup, k=5):
    """
    Real lexical retrieval baseline
    """
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # top k by score
    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:k]

    return [id_lookup[i] for i in top_indices]


def build_semantic_index(agents, model):
    """
    ChromaDB semantic index
    """
    print(f"\n🔨 Building semantic index for {len(agents)} agents...")

    client = chromadb.Client(
        Settings(anonymized_telemetry=False)
    )

    try:
        client.delete_collection("fair_benchmark_agents")
    except Exception:
        pass

    collection = client.create_collection(
        name="fair_benchmark_agents",
        metadata={"hnsw:space": "cosine"}
    )

    batch_size = 500
    for i in range(0, len(agents), batch_size):
        batch = agents[i:i + batch_size]
        docs = [build_agent_text(a) for a in batch]
        ids = [a["agent_id"] for a in batch]
        embeddings = model.encode(
            docs,
            show_progress_bar=False
        ).tolist()

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=docs,
            metadatas=[
                {"agent_id": a["agent_id"]}
                for a in batch
            ]
        )

        if (i + batch_size) % 5000 == 0 or (i + batch_size) >= len(agents):
            print(f"   Indexed {min(i + batch_size, len(agents))}/{len(agents)}")

    print(f"✅ Semantic index built — {collection.count()} agents indexed")
    return collection, client


def semantic_search(query, collection, model, k=5):
    """
    Semantic retrieval
    """
    emb = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[emb],
        n_results=k,
        include=["metadatas", "distances"]
    )

    if not results or not results["ids"][0]:
        return []

    return [m["agent_id"] for m in results["metadatas"][0]]


# ============================================================
# EVALUATION
# ============================================================

def evaluate_method(name, search_fn, queries, relevant_map):
    """
    Generic evaluator for any search function
    """
    top1 = 0
    top3 = 0
    topk = 0
    mrr = 0.0
    latencies = []

    evaluated = 0
    skipped = 0

    print(f"\n🧪 Evaluating {name}...")

    for i, q in enumerate(queries):
        query_text = q["query"]
        expected_domain = q["expected_domain"]

        relevant_ids = relevant_map.get(expected_domain, [])

        if not relevant_ids:
            skipped += 1
            continue

        evaluated += 1

        t0 = time.perf_counter()
        results = search_fn(query_text, TOP_K)
        latencies.append((time.perf_counter() - t0) * 1000)

        # hit if ANY relevant agent appears
        hits = [r for r in results if r in relevant_ids]
        if hits:
            topk += 1
            rank = results.index(hits[0]) + 1
            mrr += 1.0 / rank
            if rank == 1:
                top1 += 1
            if rank <= 3:
                top3 += 1

        if (i + 1) % 500 == 0:
            print(f"   {name}: {i + 1}/{len(queries)}")

    def pct(n):
        return round(n / evaluated, 4) if evaluated else 0

    result = {
        "evaluated_queries": evaluated,
        "skipped_queries": skipped,
        "top1_accuracy": pct(top1),
        "top3_recall": pct(top3),
        f"top{TOP_K}_recall": pct(topk),
        "mrr": round(mrr / evaluated, 4) if evaluated else 0,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "p99_latency_ms": percentile(latencies, 99),
    }

    return result


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 65)
    print("⚖️ MYCELIUM — FAIR BENCHMARK")
    print("=" * 65)

    # Load data
    print("\n📂 Loading data...")
    agents = load_json(AGENTS_FILE)
    queries = load_json(QUERIES_FILE)
    print(f"   Agents:  {len(agents)}")
    print(f"   Queries: {len(queries)}")

    # Build domain relevance map
    print("\n🗺️ Building domain map...")
    domain_map = build_domain_map(agents)
    print(f"   Domains mapped: {len(domain_map)}")

    # 1. Naive keyword
    naive_result = evaluate_method(
        "Naive Keyword",
        lambda q, k: naive_keyword_search(q, agents, k),
        queries,
        domain_map
    )

    # 2. BM25
    bm25, id_lookup = build_bm25_index(agents)
    bm25_result = evaluate_method(
        "BM25 Lexical",
        lambda q, k: bm25_search(q, bm25, id_lookup, k),
        queries,
        domain_map
    )

    # 3. Semantic
    print(f"\n🤖 Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("   Model loaded ✅")

    collection, client = build_semantic_index(agents, model)

    semantic_result = evaluate_method(
        "Semantic",
        lambda q, k: semantic_search(q, collection, model, k),
        queries,
        domain_map
    )

    # Print comparison
    print("\n")
    print("=" * 65)
    print("📊 FAIR BENCHMARK RESULTS")
    print("=" * 65)

    methods = {
        "Naive Keyword": naive_result,
        "BM25 Lexical": bm25_result,
        "Semantic": semantic_result
    }

    print(f"\n{'Method':<18} {'Top1':>8} {'Top3':>8} {'MRR':>8} {'Avg ms':>10} {'P95 ms':>10}")
    print("-" * 65)

    for method_name, res in methods.items():
        print(
            f"{method_name:<18} "
            f"{res['top1_accuracy']:>8.4f} "
            f"{res['top3_recall']:>8.4f} "
            f"{res['mrr']:>8.4f} "
            f"{res['avg_latency_ms']:>10.2f} "
            f"{res['p95_latency_ms']:>10.2f}"
        )

    # Save
    final = {
        "benchmark": "fair_v1",
        "timestamp": timestamp(),
        "agents_file": AGENTS_FILE,
        "queries_file": QUERIES_FILE,
        "top_k": TOP_K,
        "naive_keyword": naive_result,
        "bm25_lexical": bm25_result,
        "semantic": semantic_result
    }

    out_file = f"{RESULTS_DIR}/fair_benchmark_{timestamp()}.json"
    save_json(out_file, final)

    print("\n")
    print("=" * 65)
    print("🔍 SUMMARY")
    print("=" * 65)
    print(
        f"Semantic vs BM25 accuracy delta: "
        f"{(semantic_result['top1_accuracy'] - bm25_result['top1_accuracy']):+.4f}"
    )
    print(
        f"Semantic vs BM25 latency delta: "
        f"{(semantic_result['avg_latency_ms'] - bm25_result['avg_latency_ms']):+.2f}ms"
    )
    print(f"📁 Saved: {out_file}")
    print("=" * 65)


if __name__ == "__main__":
    main()