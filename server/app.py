"""
🍄 Mycelium Registry Server v0.2.0
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================
# GLOBALS
# ============================================================

agents_db: dict[str, dict] = {}
messages_queue: list[dict] = []
semantic_engine = None
SEMANTIC_ENABLED = False

# Query result cache
_query_cache: dict[str, list] = {}
_CACHE_MAX_SIZE = 500


# ============================================================
# CACHE HELPERS
# ============================================================

def cache_get(query: str, limit: int) -> list | None:
    key = f"{query.lower().strip()}:{limit}"
    return _query_cache.get(key)


def cache_set(query: str, limit: int, results: list):
    global _query_cache
    if len(_query_cache) >= _CACHE_MAX_SIZE:
        oldest_key = next(iter(_query_cache))
        del _query_cache[oldest_key]
    key = f"{query.lower().strip()}:{limit}"
    _query_cache[key] = results


def cache_invalidate():
    global _query_cache
    _query_cache = {}


# ============================================================
# STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize heavy resources ONCE at startup."""
    global semantic_engine, SEMANTIC_ENABLED

    print("\n🍄 Starting Mycelium Registry Server...\n")

    try:
        from mycelium.discovery.semantic import SemanticSearchEngine
        semantic_engine = SemanticSearchEngine()
        SEMANTIC_ENABLED = True
        print("✅ Semantic search enabled (ChromaDB)")
    except Exception as e:
        semantic_engine = None
        SEMANTIC_ENABLED = False
        print(f"⚠️ Semantic search disabled: {e}")

    yield

    print("👋 Registry shutting down.")


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="🍄 Mycelium Registry",
    description="The networking protocol for AI agents.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELS
# ============================================================

class RegisterRequest(BaseModel):
    agent_id: str
    name: str
    description: str
    version: str = "0.1.0"
    author: Optional[str] = None
    capabilities: list[dict] = []
    endpoint: Optional[str] = None
    pricing: dict = {
        "model": "free",
        "amount": 0.0,
        "currency": "USD"
    }
    languages: list[str] = ["english"]
    tags: list[str] = []
    trust_score: float = 0.0
    total_requests_served: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: Optional[float] = None
    registered_at: Optional[str] = None
    last_seen: Optional[str] = None
    status: str = "online"
    protocol_version: str = "0.1.0"


class MessageRequest(BaseModel):
    envelope: dict
    payload: dict = {}
    meta: dict = {}
    auth: dict = {}


# ============================================================
# ROUTES — REGISTRATION
# ============================================================

@app.post("/api/v1/agents/register")
async def register_agent(agent: RegisterRequest):
    """Register a new agent on the Mycelium network."""
    agent_data = agent.model_dump()
    agent_data["registered_at"] = datetime.now(
        timezone.utc
    ).isoformat()
    agent_data["last_seen"] = datetime.now(
        timezone.utc
    ).isoformat()
    agent_data["status"] = "online"

    agents_db[agent.agent_id] = agent_data

    # Index in semantic engine
    if SEMANTIC_ENABLED and semantic_engine:
        semantic_engine.index_agent(agent_data)
        print(f"🧠 Indexed: {agent.name}")

    # Invalidate cache — new agent added
    cache_invalidate()

    return {
        "status": "registered",
        "agent_id": agent.agent_id,
        "message": f"Agent '{agent.name}' registered! 🍄",
        "total_agents_on_network": len(agents_db),
        "semantic_indexed": SEMANTIC_ENABLED,
    }


@app.delete("/api/v1/agents/{agent_id}")
async def deregister_agent(agent_id: str):
    """Remove an agent from the network."""
    if agent_id not in agents_db:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )

    name = agents_db[agent_id]["name"]
    del agents_db[agent_id]

    # Remove from semantic index
    if SEMANTIC_ENABLED and semantic_engine:
        semantic_engine.remove_agent(agent_id)

    # Invalidate cache
    cache_invalidate()

    return {
        "status": "deregistered",
        "message": f"Agent '{name}' removed."
    }


# ============================================================
# ROUTES — DISCOVERY
# ============================================================

@app.get("/api/v1/agents")
async def list_agents(
    limit: int = Query(default=50, le=200),
    status: Optional[str] = Query(default=None),
):
    """List all agents on the network."""
    agents = list(agents_db.values())

    if status:
        agents = [
            a for a in agents
            if a.get("status") == status
        ]

    return {
        "agents": agents[:limit],
        "total": len(agents[:limit]),
        "network_size": len(agents_db),
    }


@app.get("/api/v1/agents/discover")
async def discover_agents(
    q: str = Query(..., description="Search query"),
    capability: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    min_trust: float = Query(default=0.0),
    limit: int = Query(default=10, le=50),
    semantic: bool = Query(
        default=True,
        description="Use semantic search"
    ),
):
    """
    Discover agents by natural language query.

    v0.2.0: Semantic vector search + result caching.
    """

    # ============================================
    # SEMANTIC SEARCH (v0.2.0)
    # ============================================
    if semantic and SEMANTIC_ENABLED and semantic_engine:

        # Check cache first
        cached = cache_get(q, limit)
        if cached is not None:
            return {
                "query": q,
                "search_type": "semantic_v2_cached",
                "agents": cached[:limit],
                "total_results": len(cached),
                "semantic_enabled": True,
                "cache_hit": True,
            }

        # Cache miss — run semantic search
        semantic_matches = semantic_engine.search(
            query=q,
            limit=limit,
            min_trust=min_trust,
        )

        results = []
        for match in semantic_matches:
            agent_id = match["agent_id"]
            if agent_id not in agents_db:
                continue

            agent_data = agents_db[agent_id].copy()

            # Capability filter
            if capability:
                cap_names = [
                    c.get("name", "")
                    for c in agent_data.get("capabilities", [])
                ]
                if capability not in cap_names:
                    continue

            # Tag filter
            if tags:
                tag_list = [t.strip() for t in tags.split(",")]
                agent_tags = agent_data.get("tags", [])
                if not any(t in agent_tags for t in tag_list):
                    continue

            agent_data["_similarity_score"] = (
                match["similarity_score"]
            )
            results.append(agent_data)

        # Store in cache
        cache_set(q, limit, results)

        return {
            "query": q,
            "search_type": "semantic_v2",
            "agents": results[:limit],
            "total_results": len(results),
            "semantic_enabled": True,
            "cache_hit": False,
        }

    # ============================================
    # KEYWORD FALLBACK (v0.1.1)
    # ============================================
    results = []
    query_lower = q.lower()
    tag_list = [t.strip() for t in tags.split(",")] \
        if tags else []

    for agent_data in agents_db.values():
        score = 0.0

        name_lower = agent_data.get("name", "").lower()
        desc_lower = agent_data.get("description", "").lower()
        agent_caps = agent_data.get("capabilities", [])
        agent_tags = [
            t.lower() for t in agent_data.get("tags", [])
        ]

        for word in query_lower.split():
            if word in name_lower:
                score += 3.0
            if word in desc_lower:
                score += 2.0
            if word in agent_tags:
                score += 2.0

        for cap in agent_caps:
            cap_name = cap.get("name", "").lower()
            cap_desc = cap.get("description", "").lower()

            if capability and capability.lower() == cap_name:
                score += 5.0

            for word in query_lower.split():
                if word in cap_name:
                    score += 3.0
                if word in cap_desc:
                    score += 1.0

        for tag in tag_list:
            if tag.lower() in agent_tags:
                score += 2.0

        agent_trust = agent_data.get("trust_score", 0.0)
        if agent_trust < min_trust:
            continue

        score += agent_trust * 0.5

        if score > 0:
            results.append((score, agent_data))

    results.sort(key=lambda x: x[0], reverse=True)
    final = [a for _, a in results[:limit]]

    return {
        "query": q,
        "search_type": "keyword_v1",
        "agents": final,
        "total_results": len(final),
        "semantic_enabled": False,
        "cache_hit": False,
    }


@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent's card by ID."""
    if agent_id not in agents_db:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )
    return agents_db[agent_id]


# ============================================================
# ROUTES — MESSAGING
# ============================================================

@app.post("/api/v1/messages/send")
async def send_message(message: MessageRequest):
    """
    Send a message from one agent to another.
    Registry acts as relay — finds target and forwards.
    """
    to_agent_id = message.envelope.get("to_agent")

    if not to_agent_id:
        raise HTTPException(
            status_code=400,
            detail="Missing 'to_agent' in envelope"
        )

    if to_agent_id not in agents_db:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{to_agent_id}' not found on network",
        )

    target_agent = agents_db[to_agent_id]
    target_endpoint = target_agent.get("endpoint")

    if not target_endpoint:
        messages_queue.append(message.model_dump())
        return {
            "status": "queued",
            "message": "Agent registered but not serving. Message queued.",
            "payload": {"outputs": {}},
        }

    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{target_endpoint}/mycelium/handle",
                json=message.model_dump(),
            )

            if response.status_code == 200:
                response_data = response.json()

                agents_db[to_agent_id][
                    "total_requests_served"
                ] = (
                    agents_db[to_agent_id].get(
                        "total_requests_served", 0
                    ) + 1
                )
                agents_db[to_agent_id]["last_seen"] = (
                    datetime.now(timezone.utc).isoformat()
                )

                return response_data

            raise HTTPException(
                status_code=502,
                detail=f"Target agent error: {response.status_code}",
            )

    except httpx.ConnectError:
        agents_db[to_agent_id]["status"] = "offline"
        raise HTTPException(
            status_code=503,
            detail=f"Agent '{target_agent['name']}' unreachable.",
        )


# ============================================================
# ROUTES — HEALTH & STATS
# ============================================================

@app.get("/")
async def root():
    """Registry info and stats."""
    return {
        "name": "🍄 Mycelium Registry",
        "version": "0.2.0",
        "protocol_version": "0.2.0",
        "total_agents": len(agents_db),
        "online_agents": sum(
            1 for a in agents_db.values()
            if a.get("status") == "online"
        ),
        "total_messages_relayed": sum(
            a.get("total_requests_served", 0)
            for a in agents_db.values()
        ),
        "semantic_enabled": SEMANTIC_ENABLED,
        "cache_size": len(_query_cache),
        "docs": "/docs",
        "message": "The networking protocol for AI agents. 🍄",
    }


@app.get("/health")
async def health_check():
    """Lightweight health check."""
    return {
        "status": "healthy",
        "agents_registered": len(agents_db),
        "semantic_enabled": SEMANTIC_ENABLED,
        "cache_entries": len(_query_cache),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.delete("/api/v1/cache")
async def clear_cache():
    """Manually clear the query cache."""
    cache_invalidate()
    return {"status": "cache_cleared"}


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )