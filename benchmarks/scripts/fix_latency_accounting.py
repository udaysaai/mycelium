"""
Instrument semantic discovery latency: does it include query EMBEDDING time?

Direct chromadb + sentence-transformers only (no SemanticSearchEngine):
- chromadb.EphemeralClient() + get_or_create_collection()
- Batched upsert with a first-batch guard.

Index-build time is excluded from all per-query measurements.
EphemeralClient has no cache, so every timed query is uncached by
construction. Measures per query: embedding_ms, search_ms, total_ms.
"""
import json
import statistics
import time
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
AGENTS_FILE = DATA_DIR / "synthetic" / "agent_cards_100k.json"
QUERIES_FILE = DATA_DIR / "queries_v2.json"
RESULTS_FILE = Path(__file__).resolve().parents[1] / "results" / "latency_breakdown.json"

SAMPLE_SIZE = 100
TOP_K = 3
BATCH_SIZE = 500
MODEL_NAME = "all-MiniLM-L6-v2"


def build_agent_text(agent: dict) -> str:
    parts = []
    if agent.get("name"):
        parts.append(f"Agent name: {agent['name']}")
    if agent.get("description"):
        parts.append(f"Description: {agent['description']}")
    caps = agent.get("capabilities", [])
    if caps:
        cap_texts = [f"{c.get('name','')}: {c.get('description','')}" for c in caps]
        parts.append(f"Capabilities: {', '.join(cap_texts)}")
    tags = agent.get("tags", [])
    if tags:
        parts.append(f"Tags: {', '.join(tags)}")
    langs = agent.get("languages", [])
    if langs:
        parts.append(f"Languages: {', '.join(langs)}")
    return " | ".join(parts)


def ms(t0):
    return (time.perf_counter() - t0) * 1000


def main():
    with open(QUERIES_FILE, encoding="utf-8") as f:
        all_queries = [q["query"] for q in json.load(f)]
    queries = all_queries[:min(SAMPLE_SIZE, len(all_queries))]
    with open(AGENTS_FILE, encoding="utf-8") as f:
        agents = json.load(f)

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        name="bench_latency_run",
        metadata={"hnsw:space": "cosine"},
    )

    # --- Index build (EXCLUDED from per-query latency) ---
    print(f"Building index over {len(agents)} agents "
          "(excluded from latency measurements)...")
    t_build = time.perf_counter()
    guard_checked = False
    for i in range(0, len(agents), BATCH_SIZE):
        batch = agents[i:i + BATCH_SIZE]
        texts = [build_agent_text(a) for a in batch]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        ids = [a["agent_id"] for a in batch]
        collection.upsert(ids=ids, embeddings=embeddings, documents=texts)
        print(f"Indexed {min(i + BATCH_SIZE, len(agents))}/{len(agents)}", end="\r")

        if not guard_checked:
            count = collection.count()
            if count == 0:
                raise RuntimeError("Index empty after first batch. Chroma error.")
            print(f"\nGuard passed: {count} agents in index after first batch")
            guard_checked = True
    print()
    build_s = time.perf_counter() - t_build

    assert collection.count() > 0, "Index empty after build"
    print(f"Index verified: {collection.count()} agents (built in {build_s:.1f}s)")
    assert collection.count() == len(agents), "Index count mismatch -- aborting."

    # --- Cold per-query measurement ---
    print(f"\nInstrumenting {len(queries)} cold queries...\n")
    rows = []
    for q in queries:
        t1 = time.perf_counter()
        vec = model.encode([q])[0]
        embedding_ms = ms(t1)

        t2 = time.perf_counter()
        collection.query(query_embeddings=[vec.tolist()], n_results=TOP_K)
        search_ms = ms(t2)

        rows.append({
            "embedding_ms": embedding_ms,
            "search_ms": search_ms,
            "total_ms": embedding_ms + search_ms,
        })

    def stats(key):
        vals = [r[key] for r in rows]
        return {
            "avg": round(statistics.mean(vals), 3),
            "p50": round(statistics.median(vals), 3),
            "p95": round(sorted(vals)[int(0.95 * len(vals)) - 1], 3),
            "max": round(max(vals), 3),
        }

    report = {k: stats(k) for k in ["embedding_ms", "search_ms", "total_ms"]}

    print("=== COLD LATENCY BREAKDOWN "
          f"({len(queries)} queries, {len(agents)} agents indexed) ===")
    for k, v in report.items():
        print(f"{k:15s} avg={v['avg']:>8.3f}  p50={v['p50']:>8.3f}  "
              f"p95={v['p95']:>8.3f}  max={v['max']:>8.3f}")

    total_avg = report["total_ms"]["avg"]
    embed_avg = report["embedding_ms"]["avg"]
    print(f"\nEmbedding share of cold total: {100 * embed_avg / total_avg:.1f}%")
    print("VERDICT: if the previously reported 14ms avg is BELOW the cold "
          f"total here ({total_avg:.1f}ms), the 14ms figure was cache-dominated "
          "and did NOT reflect per-query embedding cost.")

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "config": {
                "agents_indexed": len(agents),
                "queries": len(queries),
                "index_build_seconds": round(build_s, 1),
                "chromadb_client": "EphemeralClient (no cache in path)",
                "model": MODEL_NAME,
                "top_k": TOP_K,
            },
            "per_query": rows,
            "summary": report,
        }, f, indent=2)
    print(f"Saved -> {RESULTS_FILE}")


if __name__ == "__main__":
    main()
