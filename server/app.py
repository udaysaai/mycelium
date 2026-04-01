"""
🍄 Mycelium Registry Server

The central hub where agents register, discover each other,
and route messages.

Run with:
    python -m server.app
    # or
    uvicorn server.app:app --reload
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="🍄 Mycelium Registry",
    description="The networking protocol for AI agents. "
                "Register, discover, and communicate.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# IN-MEMORY STORAGE (Replace with DB later)
# ============================================================

agents_db: dict[str, dict] = {}  # agent_id -> agent card
messages_queue: list[dict] = []  # pending messages


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
    pricing: dict = {"model": "free", "amount": 0.0, "currency": "USD"}
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
    agent_data["registered_at"] = datetime.now(timezone.utc).isoformat()
    agent_data["last_seen"] = datetime.now(timezone.utc).isoformat()
    agent_data["status"] = "online"

    agents_db[agent.agent_id] = agent_data

    return {
        "status": "registered",
        "agent_id": agent.agent_id,
        "message": f"Agent '{agent.name}' successfully registered on Mycelium! 🍄",
        "total_agents_on_network": len(agents_db),
    }


@app.delete("/api/v1/agents/{agent_id}")
async def deregister_agent(agent_id: str):
    """Remove an agent from the network."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")

    name = agents_db[agent_id]["name"]
    del agents_db[agent_id]

    return {"status": "deregistered", "message": f"Agent '{name}' removed from network."}


# ============================================================
# ROUTES — DISCOVERY
# ============================================================


# NEW ORDER (CORRECT):

@app.get("/api/v1/agents")
async def list_agents(
    limit: int = Query(default=50, le=200),
    status: Optional[str] = Query(default=None),
):
    """List all agents on the network."""
    agents = list(agents_db.values())

    if status:
        agents = [a for a in agents if a.get("status") == status]

    agents = agents[:limit]

    return {
        "agents": agents,
        "total": len(agents),
        "network_size": len(agents_db),
    }


@app.get("/api/v1/agents/discover")          # ← PEHLE YEH
async def discover_agents(
    q: str = Query(..., description="Search query"),
    capability: Optional[str] = Query(default=None),
    tags: Optional[str] = Query(default=None),
    min_trust: float = Query(default=0.0),
    limit: int = Query(default=10, le=50),
):
    """
    Discover agents by natural language query, capability, or tags.
    """
    results = []
    query_lower = q.lower()
    tag_list = tags.split(",") if tags else []

    for agent_data in agents_db.values():
        score = 0.0

        name_lower = agent_data.get("name", "").lower()
        desc_lower = agent_data.get("description", "").lower()

        for word in query_lower.split():
            if word in name_lower:
                score += 3.0
            if word in desc_lower:
                score += 2.0

        agent_caps = agent_data.get("capabilities", [])
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

        agent_tags = [t.lower() for t in agent_data.get("tags", [])]
        for word in query_lower.split():
            if word in agent_tags:
                score += 2.0

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
    agents = [agent for _, agent in results[:limit]]

    return {
        "query": q,
        "agents": agents,
        "total_results": len(agents),
    }


@app.get("/api/v1/agents/{agent_id}")        # ← PHIR YEH
async def get_agent(agent_id: str):
    """Get a specific agent's card."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agents_db[agent_id]


# ============================================================
# ROUTES — MESSAGING
# ============================================================


@app.post("/api/v1/messages/send")
async def send_message(message: MessageRequest):
    """
    Send a message from one agent to another.

    The registry acts as a relay — finds the target agent
    and forwards the message.
    """
    to_agent_id = message.envelope.get("to_agent")
    from_agent_id = message.envelope.get("from_agent")

    if not to_agent_id:
        raise HTTPException(status_code=400, detail="Missing 'to_agent' in envelope")

    if to_agent_id not in agents_db:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{to_agent_id}' not found on network",
        )

    target_agent = agents_db[to_agent_id]
    target_endpoint = target_agent.get("endpoint")

    if not target_endpoint:
        # Agent is registered but not serving
        # Store message in queue for later delivery
        messages_queue.append(message.model_dump())
        return {
            "status": "queued",
            "message": "Agent is registered but not currently serving. Message queued.",
            "payload": {"outputs": {}},
        }

    # Forward message to target agent
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{target_endpoint}/mycelium/handle",
                json=message.model_dump(),
            )

            if response.status_code == 200:
                response_data = response.json()

                # Update stats
                if to_agent_id in agents_db:
                    agents_db[to_agent_id]["total_requests_served"] = (
                        agents_db[to_agent_id].get("total_requests_served", 0) + 1
                    )
                    agents_db[to_agent_id]["last_seen"] = (
                        datetime.now(timezone.utc).isoformat()
                    )

                return response_data
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Target agent returned error: {response.status_code}",
                )

    except httpx.ConnectError:
        # Agent endpoint unreachable
        agents_db[to_agent_id]["status"] = "offline"
        raise HTTPException(
            status_code=503,
            detail=f"Agent '{target_agent['name']}' is unreachable.",
        )


# ============================================================
# ROUTES — HEALTH & STATS
# ============================================================


@app.get("/")
async def root():
    """Welcome to Mycelium!"""
    return {
        "name": "🍄 Mycelium Registry",
        "version": "0.1.0",
        "protocol_version": "0.1.0",
        "total_agents": len(agents_db),
        "online_agents": sum(
            1 for a in agents_db.values() if a.get("status") == "online"
        ),
        "total_messages_relayed": sum(
            a.get("total_requests_served", 0) for a in agents_db.values()
        ),
        "docs": "/docs",
        "message": "The networking protocol for AI agents. 🍄",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents_registered": len(agents_db),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("\n🍄 Starting Mycelium Registry Server...\n")
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )