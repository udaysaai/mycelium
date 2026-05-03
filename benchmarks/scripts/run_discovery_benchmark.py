import json
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def save_json(path: str, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def timestamp():
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def keyword_search(agents, query):
    q = query.lower()
    scored = []

    for agent in agents:
        score = 0
        name = agent["name"].lower()
        desc = agent["description"].lower()
        tags = [t.lower() for t in agent.get("tags", [])]

        if any(word in name for word in q.split()):
            score += 3
        if any(word in desc for word in q.split()):
            score += 2
        if any(word in tags for word in q.split()):
            score += 2

        for cap in agent.get("capabilities", []):
            cap_name = cap.get("name", "").lower()
            cap_desc = cap.get("description", "").lower()
            if any(word in cap_name for word in q.split()):
                score += 3
            if any(word in cap_desc for word in q.split()):
                score += 1

        if score > 0:
            scored.append((score, agent))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:5]]


def evaluate(results, expected_domain):
    top1 = 0
    top3 = 0

    domains = []
    for r in results[:3]:
        tags = r.get("tags", [])
        domains.extend(tags)

    if results:
        if expected_domain in results[0].get("tags", []):
            top1 = 1

    if expected_domain in domains:
        top3 = 1

    return top1, top3


def main():
    agents = load_json("benchmarks/data/synthetic/agent_cards_1k.json")
    queries = load_json("benchmarks/data/synthetic/queries_1k.json")

    top1_hits = 0
    top3_hits = 0
    latencies = []
    domain_stats = defaultdict(lambda: {"count": 0, "top1": 0, "top3": 0})

    for item in queries:
        query = item["query"]
        expected_domain = item["expected_domain"]

        start = time.perf_counter()
        results = keyword_search(agents, query)
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

        top1, top3 = evaluate(results, expected_domain)
        top1_hits += top1
        top3_hits += top3

        domain_stats[expected_domain]["count"] += 1
        domain_stats[expected_domain]["top1"] += top1
        domain_stats[expected_domain]["top3"] += top3

    total = len(queries)

    summary = {
        "benchmark": "discovery_keyword_v1",
        "agents": len(agents),
        "queries": total,
        "top1_accuracy": round(top1_hits / total, 4),
        "top3_recall": round(top3_hits / total, 4),
        "latency_ms": {
            "avg": round(sum(latencies) / len(latencies), 3),
            "min": round(min(latencies), 3),
            "max": round(max(latencies), 3),
        },
        "domains": {},
    }

    for domain, stats in domain_stats.items():
        count = stats["count"]
        summary["domains"][domain] = {
            "count": count,
            "top1_accuracy": round(stats["top1"] / count, 4),
            "top3_recall": round(stats["top3"] / count, 4),
        }

    out = f"benchmarks/results/discovery/keyword_{timestamp()}.json"
    save_json(out, summary)

    print("✅ Discovery benchmark complete")
    print(f"Top-1 Accuracy: {summary['top1_accuracy']}")
    print(f"Top-3 Recall:   {summary['top3_recall']}")
    print(f"Avg Latency ms: {summary['latency_ms']['avg']}")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()