"""
🧠 Mycelium Semantic Discovery Benchmark
Compares: Keyword Search vs Semantic Search
"""

import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ---- utils inline ----
def save_json(path: str, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")
# ---- utils end ----


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_FILE = "benchmarks/data/synthetic/agent_cards_1k.json"
QUERIES_FILE = "benchmarks/data/synthetic/queries_1k.json"
RESULTS_DIR = "benchmarks/results/discovery"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5


# ============================================================
# KEYWORD SEARCH (Baseline)
# ============================================================

def keyword_search(query: str, agents: list, k: int = 5) -> list:
    """Simple keyword matching — baseline."""
    query_words = set(query.lower().split())
    scored = []

    for agent in agents:
        score = 0.0
        name = agent.get("name", "").lower()
        desc = agent.get("description", "").lower()
        caps = " ".join(
            c.get("name", "") + " " + c.get("description", "")
            for c in agent.get("capabilities", [])
        ).lower()
        tags = " ".join(agent.get("tags", [])).lower()

        full_text = f"{name} {desc} {caps} {tags}"

        for word in query_words:
            if word in full_text:
                score += 1.0

        if score > 0:
            scored.append((score, agent["agent_id"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [aid for _, aid in scored[:k]]


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def build_agent_text(agent: dict) -> str:
    """Rich text for embedding."""
    parts = []

    if agent.get("name"):
        parts.append(f"Agent: {agent['name']}")
    if agent.get("description"):
        parts.append(f"Description: {agent['description']}")

    caps = agent.get("capabilities", [])
    if caps:
        cap_text = ", ".join(
            f"{c.get('name', '')}: {c.get('description', '')}"
            for c in caps
        )
        parts.append(f"Capabilities: {cap_text}")

    tags = agent.get("tags", [])
    if tags:
        parts.append(f"Tags: {', '.join(tags)}")

    return " | ".join(parts)


def build_semantic_index(agents: list, model):
    """Build ChromaDB index for semantic search."""
    print(f"\n🔨 Building semantic index for {len(agents)} agents...")

    client = chromadb.Client(
        Settings(anonymized_telemetry=False)
    )

    # Fresh collection
    try:
        client.delete_collection("benchmark_agents")
    except Exception:
        pass

    collection = client.create_collection(
        name="benchmark_agents",
        metadata={"hnsw:space": "cosine"}
    )

    # Batch embed
    batch_size = 100
    for i in range(0, len(agents), batch_size):
        batch = agents[i:i + batch_size]
        texts = [build_agent_text(a) for a in batch]
        ids = [a["agent_id"] for a in batch]

        embeddings = model.encode(
            texts,
            show_progress_bar=False
        ).tolist()

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {"agent_id": a["agent_id"],
                 "name": a.get("name", "")}
                for a in batch
            ]
        )

        if (i // batch_size + 1) % 5 == 0:
            print(f"   Indexed {min(i + batch_size, len(agents))}/{len(agents)}")

    print(f"✅ Index built — {collection.count()} agents indexed")
    return collection, client


def semantic_search(
    query: str,
    collection,
    model,
    k: int = 5
) -> list:
    """Semantic vector search."""
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["metadatas", "distances"]
    )

    if not results or not results["ids"][0]:
        return []

    return [
        meta["agent_id"]
        for meta in results["metadatas"][0]
    ]


# ============================================================
# EVALUATION
# ============================================================

def evaluate(queries, agents, collection, model, k=5):
    """Run both keyword and semantic, compute metrics."""

    # Domain → agent_ids mapping bana
    domain_to_agents = {}
    for agent in agents:
        tags = [t.lower() for t in agent.get("tags", [])]
        name = agent.get("name", "").lower()
        desc = agent.get("description", "").lower()
        caps = " ".join(
            c.get("name", "") + " " + c.get("description", "")
            for c in agent.get("capabilities", [])
        ).lower()

        # Har domain ke liye agents collect karo
        for domain in ["weather", "finance", "legal",
                        "medical", "travel", "food",
                        "education", "sports", "tech",
                        "crypto", "translate", "search",
                        "code", "music", "news"]:
            if (domain in tags or domain in name or
                    domain in desc or domain in caps):
                if domain not in domain_to_agents:
                    domain_to_agents[domain] = []
                domain_to_agents[domain].append(
                    agent["agent_id"]
                )

    keyword_top1 = 0
    keyword_top3 = 0
    keyword_topk = 0
    keyword_latencies = []

    semantic_top1 = 0
    semantic_top3 = 0
    semantic_topk = 0
    semantic_latencies = []

    mrr_keyword = 0.0
    mrr_semantic = 0.0

    skipped = 0
    evaluated = 0
    total = len(queries)

    print(f"\n🧪 Running evaluation on {total} queries...")

    for i, q in enumerate(queries):
        query_text = q["query"]
        expected_domain = q.get("expected_domain", "")

        # Domain ke agents dhundho
        relevant_ids = domain_to_agents.get(
            expected_domain.lower(), []
        )

        if not relevant_ids:
            skipped += 1
            continue

        evaluated += 1

        # ---- KEYWORD ----
        t0 = time.perf_counter()
        kw_results = keyword_search(query_text, agents, k)
        keyword_latencies.append(
            (time.perf_counter() - t0) * 1000
        )

        # Check if ANY relevant agent in results
        kw_hits = [r for r in kw_results if r in relevant_ids]
        if kw_hits:
            keyword_topk += 1
            rank = kw_results.index(kw_hits[0]) + 1
            mrr_keyword += 1.0 / rank
            if rank == 1:
                keyword_top1 += 1
            if rank <= 3:
                keyword_top3 += 1

        # ---- SEMANTIC ----
        t0 = time.perf_counter()
        sem_results = semantic_search(
            query_text, collection, model, k
        )
        semantic_latencies.append(
            (time.perf_counter() - t0) * 1000
        )

        # Check if ANY relevant agent in results
        sem_hits = [r for r in sem_results if r in relevant_ids]
        if sem_hits:
            semantic_topk += 1
            rank = sem_results.index(sem_hits[0]) + 1
            mrr_semantic += 1.0 / rank
            if rank == 1:
                semantic_top1 += 1
            if rank <= 3:
                semantic_top3 += 1

        if (i + 1) % 100 == 0:
            print(f"   Progress: {i + 1}/{total} "
                  f"(evaluated: {evaluated}, "
                  f"skipped: {skipped})")

    print(f"\n   ✅ Evaluated: {evaluated} queries")
    print(f"   ⏭️  Skipped:   {skipped} queries "
          f"(domain not in agent corpus)")

    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0

    def pct(n):
        return round(n / evaluated, 4) if evaluated else 0

    return {
        "total_queries": total,
        "evaluated_queries": evaluated,
        "skipped_queries": skipped,
        "top_k": k,
        "keyword": {
            "top1_accuracy": pct(keyword_top1),
            "top3_recall": pct(keyword_top3),
            f"top{k}_recall": pct(keyword_topk),
            "mrr": round(mrr_keyword / evaluated, 4)
            if evaluated else 0,
            "avg_latency_ms": avg(keyword_latencies),
            "p50_latency_ms": round(
                sorted(keyword_latencies)[
                    len(keyword_latencies) // 2
                ], 2
            ) if keyword_latencies else 0,
            "p95_latency_ms": round(
                sorted(keyword_latencies)[
                    int(len(keyword_latencies) * 0.95)
                ], 2
            ) if keyword_latencies else 0,
        },
        "semantic": {
            "top1_accuracy": pct(semantic_top1),
            "top3_recall": pct(semantic_top3),
            f"top{k}_recall": pct(semantic_topk),
            "mrr": round(mrr_semantic / evaluated, 4)
            if evaluated else 0,
            "avg_latency_ms": avg(semantic_latencies),
            "p50_latency_ms": round(
                sorted(semantic_latencies)[
                    len(semantic_latencies) // 2
                ], 2
            ) if semantic_latencies else 0,
            "p95_latency_ms": round(
                sorted(semantic_latencies)[
                    int(len(semantic_latencies) * 0.95)
                ], 2
            ) if semantic_latencies else 0,
        },
        "improvement": {}
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("🍄 MYCELIUM — Keyword vs Semantic Benchmark")
    print("=" * 60)

    # Load data
    print("\n📂 Loading data...")
    agents = load_json(AGENTS_FILE)
    queries = load_json(QUERIES_FILE)
    print(f"   Agents:  {len(agents)}")
    print(f"   Queries: {len(queries)}")

    # Load model
    print(f"\n🤖 Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("   Model loaded ✅")

    # Build semantic index
    collection, client = build_semantic_index(agents, model)

    # Run evaluation
    results = evaluate(queries, agents, collection, model, TOP_K)

    # Calculate improvement
    kw = results["keyword"]
    sem = results["semantic"]

    results["improvement"] = {
        "top1_accuracy": round(
            sem["top1_accuracy"] - kw["top1_accuracy"], 4
        ),
        "top3_recall": round(
            sem["top3_recall"] - kw["top3_recall"], 4
        ),
        "mrr": round(sem["mrr"] - kw["mrr"], 4),
        "latency_cost_ms": round(
            sem["avg_latency_ms"] - kw["avg_latency_ms"], 2
        ),
    }

    # Add metadata
    results["metadata"] = {
        "timestamp": timestamp(),
        "model": MODEL_NAME,
        "dataset": "synthetic_v1",
        "agents_count": len(agents),
        "queries_count": len(queries),
        "mycelium_version": "0.2.0",
    }

    # Save results
    out_file = f"{RESULTS_DIR}/semantic_vs_keyword_{timestamp()}.json"
    save_json(out_file, results)

    # Print results
    print("\n")
    print("=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)

    print(f"\n{'Metric':<25} {'Keyword':>12} {'Semantic':>12} {'Delta':>10}")
    print("-" * 60)

    metrics = [
        ("Top-1 Accuracy", "top1_accuracy", True),
        ("Top-3 Recall", "top3_recall", True),
        (f"Top-{TOP_K} Recall", f"top{TOP_K}_recall", True),
        ("MRR", "mrr", True),
        ("Avg Latency (ms)", "avg_latency_ms", False),
        ("P95 Latency (ms)", "p95_latency_ms", False),
    ]

    for label, key, higher_better in metrics:
        kv = kw.get(key, 0)
        sv = sem.get(key, 0)
        delta = sv - kv
        arrow = "📈" if (
            (higher_better and delta > 0) or
            (not higher_better and delta < 0)
        ) else "📉"

        print(
            f"{label:<25} {kv:>12.4f} {sv:>12.4f} "
            f"{delta:>+9.4f} {arrow}"
        )

    print("\n")
    print("=" * 60)
    print("🔍 SUMMARY")
    print("=" * 60)

    imp = results["improvement"]
    top1_pct = abs(imp["top1_accuracy"]) * 100

    if imp["top1_accuracy"] > 0:
        print(f"✅ Semantic search is {top1_pct:.1f}% more accurate")
    else:
        print(f"⚠️  Keyword search performed better by {top1_pct:.1f}%")

    lat_cost = imp["latency_cost_ms"]
    print(f"⏱️  Semantic costs {lat_cost:.1f}ms extra latency per query")
    print(f"📁 Results saved: {out_file}")
    print(f"\n🍄 Mycelium Benchmark v1 Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()