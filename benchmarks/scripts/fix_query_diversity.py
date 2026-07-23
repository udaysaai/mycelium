"""
Verify queries_v2.json is genuinely diverse and non-circular.

- Flags query pairs with embedding cosine similarity > 0.85 as near-duplicates.
- Reports overall AND per-category similarity statistics.
- Clusters any remaining near-duplicate pairs to expose repeated
  sentence skeletons (the root cause of the previous 143 flagged pairs).
- Checks each query against its target agent's description (circularity).
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
QUERIES_FILE = DATA_DIR / "queries_v2.json"
AGENTS_FILE = DATA_DIR / "synthetic" / "agent_cards_100k.json"

DUPLICATE_THRESHOLD = 0.85
MODEL_NAME = "all-MiniLM-L6-v2"  # same model as production discovery


def cluster_pairs(pairs, n):
    """Union-find over near-duplicate pairs -> connected components."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j, _ in pairs:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    clusters = defaultdict(list)
    involved = {i for i, j, _ in pairs} | {j for i, j, _ in pairs}
    for idx in involved:
        clusters[find(idx)].append(idx)
    return sorted(clusters.values(), key=len, reverse=True)


def main():
    with open(QUERIES_FILE, encoding="utf-8") as f:
        queries = json.load(f)
    texts = [q["query"] for q in queries]
    cats = [q["category"] for q in queries]

    print(f"Loaded {len(texts)} queries; embedding with {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    emb = np.asarray(
        model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    )

    # Full pairwise cosine similarity (normalized => dot product).
    sim = emb @ emb.T
    n = len(texts)
    iu = np.triu_indices(n, k=1)
    pair_sims = sim[iu]

    mask = pair_sims > DUPLICATE_THRESHOLD
    dup_idx = np.where(mask)[0]
    dup_pairs = [(int(iu[0][k]), int(iu[1][k]), float(pair_sims[k])) for k in dup_idx]

    exact_unique = len(set(texts))

    print("\n=== QUERY DIVERSITY REPORT (overall) ===")
    print(f"Total queries:            {n}")
    print(f"Exact-text unique:        {exact_unique}")
    print(f"Avg pairwise similarity:  {pair_sims.mean():.4f}")
    print(f"Min pairwise similarity:  {pair_sims.min():.4f}")
    print(f"Max pairwise similarity:  {pair_sims.max():.4f}")
    print(f"Near-duplicate pairs (> {DUPLICATE_THRESHOLD}): {len(dup_pairs)}")

    # --- Per-category breakdown ---
    print("\n=== PER-CATEGORY BREAKDOWN ===")
    print(f"{'category':15s} {'count':>6s} {'avg sim':>9s} {'max sim':>9s} {'dups':>6s}")
    by_cat_idx = defaultdict(list)
    for idx, c in enumerate(cats):
        by_cat_idx[c].append(idx)
    dup_count_by_cat = defaultdict(int)
    for i, j, _ in dup_pairs:
        if cats[i] == cats[j]:
            dup_count_by_cat[cats[i]] += 1
        else:
            dup_count_by_cat["(cross-category)"] += 1
    for cat in sorted(by_cat_idx):
        idxs = by_cat_idx[cat]
        if len(idxs) < 2:
            print(f"{cat:15s} {len(idxs):>6d} {'--':>9s} {'--':>9s} "
                  f"{dup_count_by_cat[cat]:>6d}")
            continue
        sub = sim[np.ix_(idxs, idxs)]
        sub_iu = np.triu_indices(len(idxs), k=1)
        sub_sims = sub[sub_iu]
        print(f"{cat:15s} {len(idxs):>6d} {sub_sims.mean():>9.4f} "
              f"{sub_sims.max():>9.4f} {dup_count_by_cat[cat]:>6d}")
    if dup_count_by_cat["(cross-category)"]:
        print(f"{'(cross-category)':15s} {'':>6s} {'':>9s} {'':>9s} "
              f"{dup_count_by_cat['(cross-category)']:>6d}")

    # --- Template-cluster report: repeated skeletons show up as clusters ---
    if dup_pairs:
        clusters = cluster_pairs(dup_pairs, n)
        print(f"\n=== TOP SEMANTIC TEMPLATE CLUSTERS ({len(clusters)} clusters) ===")
        for rank, members in enumerate(clusters[:10], 1):
            print(f"\nCluster {rank}: {len(members)} queries "
                  f"(category: {cats[members[0]]})")
            for idx in sorted(members)[:6]:
                print(f"  Q{queries[idx]['query_id']}: {texts[idx][:75]!r}")
            if len(members) > 6:
                print(f"  ... and {len(members) - 6} more")
        print("\nEach cluster above is one sentence skeleton reworded -- "
              "replace with distinct task variants in fix_ground_truth.py.")
    else:
        print("\nNo semantic template clusters remain.")

    # --- Anti-circularity check: query vs its target agent's description ---
    with open(AGENTS_FILE, encoding="utf-8") as f:
        descriptions = {a["agent_id"]: a["description"] for a in json.load(f)}
    desc_texts = [descriptions[q["target_agent_id"]] for q in queries]
    desc_emb = np.asarray(
        model.encode(desc_texts, normalize_embeddings=True, show_progress_bar=True)
    )
    q_to_desc = np.sum(emb * desc_emb, axis=1)
    print("\n=== CIRCULARITY CHECK (query vs target description) ===")
    print(f"Avg similarity: {q_to_desc.mean():.4f}  (should be moderate, NOT >0.85)")
    print(f"Max similarity: {q_to_desc.max():.4f}")
    echoes = int((q_to_desc > DUPLICATE_THRESHOLD).sum())
    print(f"Queries that echo their description (> {DUPLICATE_THRESHOLD}): {echoes}")
    if echoes:
        print("WARNING: some queries are still paraphrases -- regenerate them.")

    verdict = "PASS" if not dup_pairs and exact_unique == n and echoes == 0 else "FAIL"
    print(f"\nVerdict: {verdict}")
    raise SystemExit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
