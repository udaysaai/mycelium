"""
Load test against the FULL 100k registry with cold/warm separation.

Endpoints (per server/app.py):
  POST   /api/v1/agents/register
  GET    /api/v1/agents/discover?q=...&limit=10&semantic=true
  GET    /api/v1/agents?limit=1   -> "network_size" is the full registry count
  DELETE /api/v1/cache            -> flush the app-level query cache

Cold/warm classification uses the "cache_hit" field in the discover JSON
response -- ground truth from the server, not a client-side heuristic.
"""
import asyncio
import json
import random
import time
from pathlib import Path
from statistics import quantiles

import httpx

BASE_URL = "http://localhost:8000"
REGISTER_ENDPOINT = f"{BASE_URL}/api/v1/agents/register"
DISCOVER_ENDPOINT = f"{BASE_URL}/api/v1/agents/discover"
AGENTS_ENDPOINT = f"{BASE_URL}/api/v1/agents"
CACHE_ENDPOINT = f"{BASE_URL}/api/v1/cache"

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
AGENTS_FILE = DATA_DIR / "synthetic" / "agent_cards_100k.json"
QUERIES_FILE = DATA_DIR / "queries_v2.json"
RESULTS_FILE = Path(__file__).resolve().parents[1] / "results" / "load_v2.json"

EXPECTED_AGENTS = 100_000
REGISTER_CONCURRENCY = 32
REQUESTS_PER_LEVEL = 3000
CONCURRENCY_LEVELS = [10, 50, 100]
WARM_REPEAT_FRACTION = 0.5  # half the traffic repeats earlier queries -> exercises cache
random.seed(42)


def pctl(values, p):
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return quantiles(sorted(values), n=100)[p - 1]


async def register_all(agents):
    sem = asyncio.Semaphore(REGISTER_CONCURRENCY)
    async with httpx.AsyncClient(timeout=30) as client:
        async def one(card):
            async with sem:
                # Full agent card IS the register payload (schema matches
                # RegisterRequest; unset fields take model defaults).
                r = await client.post(REGISTER_ENDPOINT, json=card)
                r.raise_for_status()
        for i in range(0, len(agents), 1000):
            batch = agents[i:i + 1000]
            await asyncio.gather(*(one(a) for a in batch))
            print(f"  registered {min(i + 1000, len(agents))}/{len(agents)}", end="\r")
    print()


async def verify_count(client):
    # "network_size" is the full registry size; "total" is just the page size.
    r = await client.get(AGENTS_ENDPOINT, params={"limit": 1})
    r.raise_for_status()
    return r.json().get("network_size", -1)


async def run_level(concurrency, query_pool):
    workload = []
    for _ in range(REQUESTS_PER_LEVEL):
        if workload and random.random() < WARM_REPEAT_FRACTION:
            workload.append(random.choice(workload))  # repeat -> likely cache hit
        else:
            workload.append(random.choice(query_pool))
    records = []
    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(timeout=30) as client:
        # Flush the app-level cache so this level starts cold.
        (await client.delete(CACHE_ENDPOINT)).raise_for_status()

        async def one(query):
            async with sem:
                t0 = time.perf_counter()
                try:
                    r = await client.get(DISCOVER_ENDPOINT, params={
                        "q": query, "limit": 10, "semantic": "true"})
                    ok = r.status_code == 200
                    # Server-reported truth, not a client-side guess.
                    cache_hit = bool(r.json().get("cache_hit", False)) if ok else False
                except Exception:
                    ok, cache_hit = False, False
                elapsed_ms = (time.perf_counter() - t0) * 1000
                records.append({"ms": elapsed_ms, "ok": ok, "cache_hit": cache_hit})

        t_start = time.perf_counter()
        await asyncio.gather(*(one(q) for q in workload))
        wall = time.perf_counter() - t_start

    cold = [r["ms"] for r in records if r["ok"] and not r["cache_hit"]]
    warm = [r["ms"] for r in records if r["ok"] and r["cache_hit"]]
    ok_count = len(cold) + len(warm)
    errors = len(records) - ok_count
    return {
        "concurrency": concurrency,
        "requests": len(records),
        "throughput_rps": round(len(records) / wall, 1),
        "error_rate_pct": round(100 * errors / len(records), 3),
        "cache_hit_rate_pct": round(100 * len(warm) / max(ok_count, 1), 1),
        "cold": {"count": len(cold),
                 "p50_ms": round(pctl(cold, 50) or 0, 2),
                 "p95_ms": round(pctl(cold, 95) or 0, 2),
                 "p99_ms": round(pctl(cold, 99) or 0, 2)},
        "warm": {"count": len(warm),
                 "p50_ms": round(pctl(warm, 50) or 0, 2),
                 "p95_ms": round(pctl(warm, 95) or 0, 2),
                 "p99_ms": round(pctl(warm, 99) or 0, 2)},
    }


async def main():
    with open(AGENTS_FILE, encoding="utf-8") as f:
        agents = json.load(f)
    with open(QUERIES_FILE, encoding="utf-8") as f:
        query_pool = [q["query"] for q in json.load(f)]

    async with httpx.AsyncClient(timeout=30) as client:
        count = await verify_count(client)

    if count < EXPECTED_AGENTS:
        print(f"Registry has {count} agents; registering full corpus of {len(agents)}...")
        await register_all(agents)
        async with httpx.AsyncClient(timeout=30) as client:
            count = await verify_count(client)

    # HARD GATE: measuring against an underpopulated registry was PROBLEM 3.
    assert count >= EXPECTED_AGENTS, (
        f"ABORT: registry has {count} agents, need {EXPECTED_AGENTS}."
    )
    print(f"Verified registry population: {count} agents. Starting load test.\n")

    results = []
    for level in CONCURRENCY_LEVELS:
        print(f"--- {level} concurrent users ---")
        res = await run_level(level, query_pool)
        results.append(res)
        print(json.dumps(res, indent=2))

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"registry_agents": count, "levels": results}, f, indent=2)
    print(f"\nSaved -> {RESULTS_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
