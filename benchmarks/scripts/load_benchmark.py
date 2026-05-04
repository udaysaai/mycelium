"""
⚡ Mycelium Load Benchmark
Tests registry performance under concurrent load.

Scenarios:
- 10 concurrent users
- 50 concurrent users
- 100 concurrent users

Metrics:
- Requests/second
- p50, p95, p99 latency
- Error rate
- Throughput
"""

import json
import time
import threading
import random
import httpx
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# CONFIG
# ============================================================

REGISTRY_URL = "http://127.0.0.1:8000"  
AGENTS_FILE = "benchmarks/data/synthetic/agent_cards_1k.json"
QUERIES_FILE = "benchmarks/data/synthetic/queries_1k.json"
RESULTS_DIR = "benchmarks/results/load"

SCENARIOS = [
    {"name": "light",   "users": 10,  "duration": 30},
    {"name": "medium",  "users": 50,  "duration": 30},
    {"name": "heavy",   "users": 100, "duration": 30},
]

SAMPLE_QUERIES = [
    "I need weather data",
    "translate text to hindi",
    "get crypto price",
    "legal document analysis",
    "medical information",
    "find a travel agent",
    "code review agent",
    "summarize text",
    "financial analysis",
    "search the web",
]


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
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p / 100)
    idx = min(idx, len(sorted_data) - 1)
    return round(sorted_data[idx], 2)


# ============================================================
# REGISTRY SETUP
# ============================================================

def check_registry():
    """Check if registry is running."""
    try:
        r = httpx.get(f"{REGISTRY_URL}/health", timeout=5)
        if r.status_code == 200:
            print(f"✅ Registry online: {REGISTRY_URL}")
            return True
    except Exception:
        pass
    print(f"❌ Registry offline: {REGISTRY_URL}")
    print("   Run: python -m server.app")
    return False


def register_agents(agents: list) -> int:
    """Register test agents on registry."""
    print(f"\n📝 Registering {len(agents)} agents...")
    success = 0

    for agent in agents:
        try:
            r = httpx.post(
                f"{REGISTRY_URL}/api/v1/agents/register",
                json=agent,
                timeout=10
            )
            if r.status_code == 200:
                success += 1
        except Exception:
            pass

    print(f"   ✅ Registered: {success}/{len(agents)}")
    return success


# ============================================================
# LOAD TEST WORKER
# ============================================================

def worker(
    worker_id: int,
    duration_sec: int,
    results: list,
    errors: list,
    lock: threading.Lock
):
    """Single worker — sends requests for duration seconds."""
    end_time = time.time() + duration_sec
    local_results = []
    local_errors = []

    while time.time() < end_time:
        query = random.choice(SAMPLE_QUERIES)

        # Random operation
        op = random.choice(["discover", "list", "health"])

        try:
            t0 = time.perf_counter()

            if op == "discover":
                r = httpx.get(
                    f"{REGISTRY_URL}/api/v1/agents/discover",
                    params={"q": query, "limit": 5},
                    timeout=10
                )
            elif op == "list":
                r = httpx.get(
                    f"{REGISTRY_URL}/api/v1/agents",
                    params={"limit": 20},
                    timeout=10
                )
            else:
                r = httpx.get(
                    f"{REGISTRY_URL}/health",
                    timeout=10
                )

            latency_ms = (time.perf_counter() - t0) * 1000

            if r.status_code == 200:
                local_results.append({
                    "op": op,
                    "latency_ms": latency_ms,
                    "status": r.status_code
                })
            else:
                local_errors.append({
                    "op": op,
                    "status": r.status_code,
                    "error": r.text[:100]
                })

        except httpx.TimeoutException:
            local_errors.append({
                "op": op,
                "status": 0,
                "error": "timeout"
            })
        except Exception as e:
            local_errors.append({
                "op": op,
                "status": 0,
                "error": str(e)[:100]
            })

    with lock:
        results.extend(local_results)
        errors.extend(local_errors)


# ============================================================
# RUN SCENARIO
# ============================================================

def run_scenario(scenario: dict) -> dict:
    """Run a single load scenario."""
    name = scenario["name"]
    users = scenario["users"]
    duration = scenario["duration"]

    print(f"\n{'='*55}")
    print(f"🔥 Scenario: {name.upper()}")
    print(f"   Users:    {users} concurrent")
    print(f"   Duration: {duration} seconds")
    print(f"{'='*55}")

    results = []
    errors = []
    lock = threading.Lock()

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=users) as executor:
        futures = [
            executor.submit(
                worker, i, duration,
                results, errors, lock
            )
            for i in range(users)
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"   Worker error: {e}")

    total_time = time.time() - start_time
    total_requests = len(results) + len(errors)

    if not results:
        print(f"   ❌ No successful requests!")
        return {
            "scenario": name,
            "users": users,
            "duration": duration,
            "total_requests": total_requests,
            "successful": 0,
            "failed": len(errors),
            "rps": 0,
            "error_rate": 1.0,
        }

    latencies = [r["latency_ms"] for r in results]

    # Per operation breakdown
    ops = defaultdict(list)
    for r in results:
        ops[r["op"]].append(r["latency_ms"])

    scenario_result = {
        "scenario": name,
        "users": users,
        "duration_sec": duration,
        "total_requests": total_requests,
        "successful": len(results),
        "failed": len(errors),
        "error_rate": round(len(errors) / total_requests, 4)
        if total_requests else 0,
        "rps": round(total_requests / total_time, 2),
        "latency": {
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "p50_ms": percentile(latencies, 50),
            "p90_ms": percentile(latencies, 90),
            "p95_ms": percentile(latencies, 95),
            "p99_ms": percentile(latencies, 99),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
        },
        "operations": {
            op: {
                "count": len(lat_list),
                "avg_ms": round(
                    sum(lat_list) / len(lat_list), 2
                )
            }
            for op, lat_list in ops.items()
        },
        "errors_sample": errors[:5]
    }

    # Print results
    print(f"\n   📊 Results:")
    print(f"   Total Requests:  {total_requests}")
    print(f"   Successful:      {len(results)}")
    print(f"   Failed:          {len(errors)}")
    print(f"   RPS:             {scenario_result['rps']}")
    print(f"   Error Rate:      {scenario_result['error_rate']*100:.1f}%")
    print(f"\n   Latency:")
    print(f"   avg:  {scenario_result['latency']['avg_ms']}ms")
    print(f"   p50:  {scenario_result['latency']['p50_ms']}ms")
    print(f"   p95:  {scenario_result['latency']['p95_ms']}ms")
    print(f"   p99:  {scenario_result['latency']['p99_ms']}ms")
    print(f"   max:  {scenario_result['latency']['max_ms']}ms")

    return scenario_result


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 55)
    print("⚡ MYCELIUM — Load Benchmark")
    print("=" * 55)

    # Check registry
    if not check_registry():
        print("\n❌ Start registry first:")
        print("   python -m server.app")
        return

    # Load agents
    print("\n📂 Loading agents...")
    agents = load_json(AGENTS_FILE)
    print(f"   Loaded: {len(agents)} agents")

    # Register agents
    registered = register_agents(agents[:200])

    if registered == 0:
        print("❌ Could not register any agents. Exiting.")
        return

    print(f"\n⏳ Waiting 2 seconds for registry to settle...")
    time.sleep(2)

    # Run all scenarios
    all_results = []

    for scenario in SCENARIOS:
        result = run_scenario(scenario)
        all_results.append(result)
        print(f"\n⏳ Cooling down 5 seconds...")
        time.sleep(5)

    # Final report
    print("\n")
    print("=" * 55)
    print("📊 LOAD BENCHMARK SUMMARY")
    print("=" * 55)
    print(f"\n{'Scenario':<10} {'Users':>6} {'RPS':>8} "
          f"{'p95ms':>8} {'p99ms':>8} {'Errors':>8}")
    print("-" * 55)

    for r in all_results:
        err_pct = f"{r['error_rate']*100:.1f}%"
        p95 = r['latency'].get('p95_ms', 0) if r.get('latency') else 0
        p99 = r['latency'].get('p99_ms', 0) if r.get('latency') else 0
        print(
            f"{r['scenario']:<10} "
            f"{r['users']:>6} "
            f"{r['rps']:>8} "
            f"{p95:>8} "
            f"{p99:>8} "
            f"{err_pct:>8}"
        )

    # Save
    final_report = {
        "benchmark": "load_v1",
        "timestamp": timestamp(),
        "registry_url": REGISTRY_URL,
        "agents_registered": registered,
        "mycelium_version": "0.2.0",
        "scenarios": all_results,
        "summary": {
            "max_rps": max(r["rps"] for r in all_results),
            "best_p95": min(
                r["latency"].get("p95_ms", 999)
                for r in all_results
                if r.get("latency")
            ),
            "max_concurrent_users": max(
                r["users"] for r in all_results
            ),
        }
    }

    out_file = f"{RESULTS_DIR}/load_{timestamp()}.json"
    save_json(out_file, final_report)

    print(f"\n{'='*55}")
    print(f"✅ Max RPS achieved: {final_report['summary']['max_rps']}")
    print(f"✅ Best p95 latency: {final_report['summary']['best_p95']}ms")
    print(f"✅ Max concurrent:   {final_report['summary']['max_concurrent_users']} users")
    print(f"📁 Saved: {out_file}")
    print(f"\n🍄 Mycelium Load Benchmark Complete!")
    print("=" * 55)


if __name__ == "__main__":
    main()