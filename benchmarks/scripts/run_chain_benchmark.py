import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import asyncio
import time
import httpx

# Configuration
BASE_URL = "http://127.0.0.1:8000"
ITERATIONS = 50
CHAIN_DEPTHS = [2, 3, 5]
HTTP_TIMEOUT = 60.0

async def setup_chain_agents(depth):
    """Registers dummy agents for the chain using direct HTTP."""
    agent_ids = []
    
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        for i in range(depth):
            agent_data = {
                "agent_id": f"chain_agent_{depth}_{i}",
                "name": f"ChainAgent_{depth}_{i}",
                "description": f"Agent {i} in a chain of depth {depth}",
                "capabilities": [{"name": f"step_{i}", "description": f"Executes step {i}"}],
                "endpoint": f"http://127.0.0.1:8001/agent{i}" 
            }
            
            response = await client.post(f"{BASE_URL}/api/v1/agents/register", json=agent_data)
            
            if response.status_code in (200, 201):
                agent_ids.append(agent_data["agent_id"])
                
    return agent_ids

async def simulate_chain_execution(depth):
    """Simulates passing a payload through 'depth' number of agents."""
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as http_client:
        for i in range(depth):
            
            # FIXED: Changed ?query= to ?q=
            endpoints = [
                ("GET", f"{BASE_URL}/api/v1/discover?q=step_{i}&limit=1"),
                ("GET", f"{BASE_URL}/api/v1/agents/discover?q=step_{i}&limit=1"),
                ("GET", f"{BASE_URL}/api/v1/agents/search?q=step_{i}&limit=1"),
                ("POST", f"{BASE_URL}/api/v1/agents/search"), 
                ("POST", f"{BASE_URL}/api/v1/discover")
            ]
            
            search_req = None
            for method, url in endpoints:
                if method == "GET":
                    search_req = await http_client.get(url)
                else:
                    search_req = await http_client.post(url, json={"q": f"step_{i}", "limit": 1})
                
                if search_req.status_code != 404:
                    break

            if search_req.status_code != 200:
                print(f"🛑 Search Error Status: {search_req.status_code}")
                print(f"🛑 Error Details: {search_req.text}")
                return False, 0
                
            data = search_req.json()
            found_agents = data.get("results") or data.get("agents") or (data if isinstance(data, list) else [])
            
            if not found_agents:
                return False, 0
                
            # Simulate network payload parsing / hop (5ms overhead)
            await asyncio.sleep(0.005) 
            
    end_time = time.time()
    return True, (end_time - start_time) * 1000

async def run_benchmark():
    print("="*50)
    print("🚀 MYCELIUM WORKFLOW CHAIN BENCHMARK")
    print("="*50)
    print(f"Target: {BASE_URL}")
    print(f"Iterations per depth: {ITERATIONS}\n")

    results = {}

    for depth in CHAIN_DEPTHS:
        print(f"Setting up Chain Depth: {depth} (e.g., A{'->Agent'* (depth-1)})")
        await setup_chain_agents(depth)
        
        await asyncio.sleep(2)
        
        success_count = 0
        latencies = []
        
        print(f"Running {ITERATIONS} iterations...")
        for _ in range(ITERATIONS):
            success, latency = await simulate_chain_execution(depth)
            if success:
                success_count += 1
                latencies.append(latency)
                
        if success_count == 0:
            print("⚠️ Chain failed completely. Check logs.")
            break
            
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        success_rate = (success_count / ITERATIONS) * 100
        
        results[depth] = {
            "avg_latency_ms": avg_latency,
            "success_rate": success_rate,
            "per_hop_latency_ms": avg_latency / depth if depth else 0
        }
        
        print(f"✅ Depth {depth} Results:")
        print(f"   - Success Rate: {success_rate}%")
        print(f"   - Total Chain Latency: {avg_latency:.2f} ms")
        print(f"   - Avg Hop Latency: {results[depth]['per_hop_latency_ms']:.2f} ms\n")

    print("📊 FINAL SUMMARY:")
    for d, res in results.items():
        print(f"Chain-{d} | Success: {res['success_rate']}% | Latency: {res['avg_latency_ms']:.2f}ms | Per-Hop: {res['per_hop_latency_ms']:.2f}ms")

if __name__ == "__main__":
    asyncio.run(run_benchmark())