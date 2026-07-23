"""
Fair benchmark v3: FAMILY-LEVEL evaluation.

WHY THIS VERSION EXISTS:
The 100k corpus contains ~12.4k-12.6k functionally equivalent agents per
capability family. Exact-ID scoring rewards only an arbitrary subset of
those equivalents: BM25/naive benefit from stable-sort tie ordering that
happens to align with the labeled subset, while semantic is penalized for
returning VALID agents from the same family that were not in the label set.
Family-level correctness measures what discovery is actually for: did the
method return an agent that CAN DO THE TASK?

Both views are reported side by side to make the metric gap explicit:
  A. family-level:  top1_family_pct / top3_family_pct / family_mrr
  B. exact-target:  top1_exact_pct / top3_exact_pct / exact_mrr

Methods (unchanged): naive keyword, BM25, semantic
(direct chromadb.EphemeralClient + SentenceTransformer; no engine class).
Same corpus, same query file, same build_agent_text for all methods.
Output: benchmarks/results/fair_v3_family_eval.json
"""
import json
import time
from pathlib import Path
from statistics import mean

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
AGENTS_FILE = DATA_DIR / "synthetic" / "agent_cards_100k.json"
QUERIES_FILE = DATA_DIR / "queries_v2.json"
RESULTS_FILE = Path(__file__).resolve().parents[1] / "results" / "fair_v3_family_eval.json"

TOP_K = 3
BATCH_SIZE = 500
MODEL_NAME = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# AGENT family derivation: keywords matched against tags -> capabilities ->
# name -> description (in that priority order). Broad families only.
# ---------------------------------------------------------------------------
FAMILY_KEYWORDS = {
    "weather": ["weather", "forecast", "temperature", "meteorolog", "climate"],
    "finance": ["finance", "forex", "currency", "exchange rate", "crypto",
                "bitcoin", "ethereum", "stock", "market", "invoice", "budget",
                "expense", "payroll", "accounting", "bookkeep"],
    "translation": ["translat", "language pair", "multilingual", "localiz"],
    "knowledge": ["wiki", "encyclopedia", "knowledge", "factual", "research",
                  "information retrieval", "question answering"],
    "support": ["support", "ticket", "helpdesk", "customer service",
                "sentiment", "complaint"],
    "hiring": ["hiring", "recruit", "candidate", "resume", "interview",
               "talent", "screening"],
    "legal": ["legal", "contract", "compliance", "law", "regulat", "clause"],
    "medical": ["medical", "health", "clinic", "patient", "prescription",
                "diagnos", "symptom", "eligibility"],
}

# ---------------------------------------------------------------------------
# QUERY category -> family normalization.
# query["category"] is used when available, then normalized here.
# ---------------------------------------------------------------------------
QUERY_FAMILY_MAP = {
    # Identity mappings: category name IS the family name.
    "weather": "weather",
    "finance": "finance",
    "translation": "translation",
    "knowledge": "knowledge",
    "support": "support",
    "hiring": "hiring",
    "legal": "legal",
    "medical": "medical",
    # wiki queries are knowledge-lookup tasks.
    "wiki": "knowledge",
    # forex / crypto / stock / market_summary are all money-domain tasks
    # served by the finance family.
    "forex": "finance",
    "crypto": "finance",
    "stock": "finance",
    "market_summary": "finance",
    # ticket / reply / issue / sentiment are customer-support sub-tasks.
    "ticket": "support",
    "reply": "support",
    "issue": "support",
    "sentiment": "support",
    # resume / interview / candidate / skills are recruiting sub-tasks.
    "resume": "hiring",
    "interview": "hiring",
    "candidate": "hiring",
    "skills": "hiring",
    # risk / prescription / eligibility / summary are clinical-workflow
    # sub-tasks in this corpus's taxonomy.
    "risk": "medical",
    "prescription": "medical",
    "eligibility": "medical",
    "summary": "medical",
}


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


def derive_agent_family(agent: dict) -> str:
    tags = " ".join(agent.get("tags", [])).lower()
    caps = " ".join(
        f"{c.get('name', '')} {c.get('description', '')}"
        for c in agent.get("capabilities", [])
    ).lower()
    name = agent.get("name", "").lower()
    desc = agent.get("description", "").lower()
    for source in (tags, caps, name, desc):
        for family, keywords in FAMILY_KEYWORDS.items():
            if any(kw in source for kw in keywords):
                return family
    return "unknown"  # never counts as a family hit


def query_family(q: dict) -> str | None:
    cat = q.get("category")
    if cat and cat in QUERY_FAMILY_MAP:
        return QUERY_FAMILY_MAP[cat]
    return None  # unmappable: excluded from evaluation, reported below


def p95(vals):
    return sorted(vals)[int(0.95 * len(vals)) - 1]


def tokenize(text):
    return text.lower().split()


def evaluate(name, rank_fn, queries, families, targets, agent_family):
    """
    rank_fn(query_text) -> ordered list of agent ids.
    Returns (summary_dict, per_query_prediction_records).
    """
    fam_top1 = fam_top3 = 0
    ex_top1 = ex_top3 = 0
    fam_rr, ex_rr, latencies = [], [], []
    predictions = []

    for q, fam, target in zip(queries, families, targets):
        t0 = time.perf_counter()
        ranked = rank_fn(q["query"])[:TOP_K]
        latencies.append((time.perf_counter() - t0) * 1000)
        pred_fams = [agent_family.get(aid, "unknown") for aid in ranked]

        # Family view: correct if the predicted agent can do the task.
        fam_rank = next((i + 1 for i, f in enumerate(pred_fams) if f == fam), None)
        if fam_rank == 1:
            fam_top1 += 1
        if fam_rank is not None:
            fam_top3 += 1
            fam_rr.append(1 / fam_rank)
        else:
            fam_rr.append(0.0)

        # Exact view: correct only if the one labeled target id appears.
        ex_rank = next((i + 1 for i, aid in enumerate(ranked) if aid == target), None)
        if ex_rank == 1:
            ex_top1 += 1
        if ex_rank is not None:
            ex_top3 += 1
            ex_rr.append(1 / ex_rank)
        else:
            ex_rr.append(0.0)

        predictions.append({
            "query_id": q["query_id"],
            "query": q["query"],
            "query_family": fam,
            "top3_agent_ids": ranked,
            "top3_families": pred_fams,
            "family_top1_hit": fam_rank == 1,
            "family_top3_hit": fam_rank is not None,
            "exact_top1_hit": ex_rank == 1,
            "exact_top3_hit": ex_rank is not None,
        })

    n = len(queries)
    summary = {
        "method": name,
        # A. family-level correctness (the valid metric for this corpus)
        "top1_family_pct": round(100 * fam_top1 / n, 1),
        "top3_family_pct": round(100 * fam_top3 / n, 1),
        "family_mrr": round(mean(fam_rr), 3),
        # B. exact-target-id correctness (kept to expose the metric's flaw)
        "top1_exact_pct": round(100 * ex_top1 / n, 1),
        "top3_exact_pct": round(100 * ex_top3 / n, 1),
        "exact_mrr": round(mean(ex_rr), 3),
        "uncached_avg_latency_ms": round(mean(latencies), 2),
        "uncached_p95_latency_ms": round(p95(latencies), 2),
        "queries": n,
    }
    return summary, predictions


def main():
    with open(AGENTS_FILE, encoding="utf-8") as f:
        agents = json.load(f)
    with open(QUERIES_FILE, encoding="utf-8") as f:
        qdata = json.load(f)

    texts = [q["query"] for q in qdata]
    assert len(texts) == len(set(texts)), \
        "Duplicate query texts detected -- cold-latency guarantee broken."

    # Label every agent with a family (unknowns stay as distractors).
    agent_family = {a["agent_id"]: derive_agent_family(a) for a in agents}
    fam_counts = {}
    for f in agent_family.values():
        fam_counts[f] = fam_counts.get(f, 0) + 1
    print("Agent family distribution:")
    for fam, c in sorted(fam_counts.items(), key=lambda x: -x[1]):
        print(f"  {fam:12s} {c}")

    # Map queries to families; drop unmappable ones (reported, not silent).
    eval_queries, families, targets, unmappable = [], [], [], []
    for q in qdata:
        fam = query_family(q)
        if fam is None:
            unmappable.append(q.get("category"))
            continue
        eval_queries.append(q)
        families.append(fam)
        targets.append(q["target_agent_id"])
    if unmappable:
        cats = sorted(set(c for c in unmappable if c))
        print(f"\nWARNING: {len(unmappable)} queries have categories with no "
              f"family mapping and are EXCLUDED from evaluation: {cats}")
    print(f"\nCorpus: {len(agents)} agents | Evaluated queries: {len(eval_queries)}\n")

    ids = [a["agent_id"] for a in agents]
    rich_texts = [build_agent_text(a) for a in agents]  # shared text basis

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        name="bench_fair_v3",
        metadata={"hnsw:space": "cosine"},
    )

    # --- Shared semantic index build (EXCLUDED from query timing) ---
    print("Building semantic index (excluded from latency)...")
    t_build = time.perf_counter()
    guard_checked = False
    for i in range(0, len(agents), BATCH_SIZE):
        batch_ids = ids[i:i + BATCH_SIZE]
        batch_texts = rich_texts[i:i + BATCH_SIZE]
        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()
        collection.upsert(ids=batch_ids, embeddings=embeddings,
                          documents=batch_texts)
        print(f"Indexed {min(i + BATCH_SIZE, len(agents))}/{len(agents)}", end="\r")
        if not guard_checked:
            count = collection.count()
            if count == 0:
                raise RuntimeError("Index empty after first batch. Chroma error.")
            print(f"\nGuard passed: {count} agents in index after first batch")
            guard_checked = True
    print()
    build_s = time.perf_counter() - t_build
    assert collection.count() == len(agents), "Index count mismatch -- aborting."
    print(f"Index verified: {collection.count()} agents (built in {build_s:.1f}s)\n")

    all_results, all_predictions = [], {}

    # --- Method 1: Naive keyword (token overlap on the SAME rich text) ---
    doc_token_sets = [set(tokenize(t)) for t in rich_texts]

    def naive_rank(query):
        qt = set(tokenize(query))
        scored = sorted(range(len(ids)),
                        key=lambda i: len(qt & doc_token_sets[i]), reverse=True)
        return [ids[i] for i in scored[:TOP_K]]

    print("Running: Naive Keyword...")
    s, p = evaluate("naive_keyword", naive_rank, eval_queries, families,
                    targets, agent_family)
    all_results.append(s)
    all_predictions["naive_keyword"] = p

    # --- Method 2: BM25 on the SAME rich text ---
    bm25 = BM25Okapi([tokenize(t) for t in rich_texts])

    def bm25_rank(query):
        scores = bm25.get_scores(tokenize(query))
        top = sorted(range(len(ids)), key=lambda i: scores[i], reverse=True)[:TOP_K]
        return [ids[i] for i in top]

    print("Running: BM25...")
    s, p = evaluate("bm25", bm25_rank, eval_queries, families,
                    targets, agent_family)
    all_results.append(s)
    all_predictions["bm25"] = p

    # --- Method 3: Semantic (embedding time INSIDE timed section) ---
    def semantic_rank(query):
        vec = model.encode([query])[0]
        res = collection.query(query_embeddings=[vec.tolist()], n_results=TOP_K)
        return res["ids"][0]

    print("Running: Semantic...")
    s, p = evaluate("semantic", semantic_rank, eval_queries, families,
                    targets, agent_family)
    all_results.append(s)
    all_predictions["semantic"] = p

    # --- Report both views side by side ---
    print("\n=== VIEW A: FAMILY-LEVEL CORRECTNESS (valid metric) ===")
    print(f"{'Method':<16}{'Top-1':>8}{'Top-3':>8}{'MRR':>8}")
    for r in all_results:
        print(f"{r['method']:<16}{r['top1_family_pct']:>7}%"
              f"{r['top3_family_pct']:>7}%{r['family_mrr']:>8}")

    print("\n=== VIEW B: EXACT-TARGET-ID CORRECTNESS (flawed metric, shown for contrast) ===")
    print(f"{'Method':<16}{'Top-1':>8}{'Top-3':>8}{'MRR':>8}")
    for r in all_results:
        print(f"{r['method']:<16}{r['top1_exact_pct']:>7}%"
              f"{r['top3_exact_pct']:>7}%{r['exact_mrr']:>8}")

    print("\n=== LATENCY (uncached) ===")
    for r in all_results:
        print(f"{r['method']:<16} avg={r['uncached_avg_latency_ms']}ms "
              f"p95={r['uncached_p95_latency_ms']}ms")

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "config": {
                "agents": len(agents),
                "queries_evaluated": len(eval_queries),
                "queries_excluded_unmappable": len(unmappable),
                "queries_file": "queries_v2.json",
                "text_basis": "identical build_agent_text output for all methods",
                "chromadb_client": "EphemeralClient (no cache in path)",
                "embedding_in_semantic_latency": True,
                "index_build_excluded": True,
                "index_build_seconds": round(build_s, 1),
                "model": MODEL_NAME,
                "top_k": TOP_K,
                "agent_family_distribution": fam_counts,
            },
            "results": all_results,
            "per_query_predictions": all_predictions,
        }, f, indent=2)
    print(f"\nSaved -> {RESULTS_FILE}")

    print(
        "\nNOTE ON METRIC VALIDITY:\n"
        "This corpus contains thousands of functionally equivalent agents per\n"
        "family (~12.4k-12.6k each). With one labeled target id among thousands\n"
        "of interchangeable agents, exact-ID scoring measures WHICH equivalent\n"
        "an algorithm happens to surface -- an artifact of tie-breaking and\n"
        "sort stability -- not whether discovery found a capable agent.\n"
        "Lexical methods can score well on exact-ID purely because stable-sort\n"
        "tie ordering aligns with the labeled subset, while semantic search is\n"
        "penalized for returning equally valid family members. Family-level\n"
        "correctness asks the question users actually care about: can the\n"
        "returned agent do the task? That is the metric to report."
    )


if __name__ == "__main__":
    main()
