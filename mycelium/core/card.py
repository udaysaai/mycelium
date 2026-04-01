"""
AgentCard — The identity document of an agent on the Mycelium network.

Think of it as an Aadhaar Card for AI agents.
Every agent on the network has a card that tells others:
- Who am I?
- What can I do?
- How to reach me?
- Can I be trusted?
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
import uuid


def generate_agent_id() -> str:
    """Generate a unique agent ID."""
    short_uuid = uuid.uuid4().hex[:12]
    return f"ag_{short_uuid}"


class PricingInfo(BaseModel):
    """How much does this agent charge?"""

    model: str = Field(
        default="free",
        description="Pricing model: 'free', 'per_request', 'subscription'",
    )
    amount: float = Field(default=0.0, description="Price amount")
    currency: str = Field(default="USD", description="Currency code")


class AgentCard(BaseModel):
    """
    The public identity of an agent on the Mycelium network.

    This is what other agents and the registry see.
    """

    # Identity
    agent_id: str = Field(default_factory=generate_agent_id)
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="What does this agent do?")
    version: str = Field(default="0.1.0")
    author: Optional[str] = Field(default=None, description="Creator email or name")

    # Capabilities
    capabilities: list[dict] = Field(
        default_factory=list,
        description="List of capability definitions",
    )

    # Network info
    endpoint: Optional[str] = Field(
        default=None,
        description="URL where this agent can be reached",
    )
    
    # Metadata
    pricing: PricingInfo = Field(default_factory=PricingInfo)
    languages: list[str] = Field(default_factory=lambda: ["english"])
    tags: list[str] = Field(default_factory=list)
    
    # Trust & reputation
    trust_score: float = Field(default=0.0, ge=0.0, le=5.0)
    total_requests_served: int = Field(default=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_response_time_ms: Optional[float] = Field(default=None)

    # Timestamps
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: str = Field(
        default="offline",
        description="'online', 'offline', 'busy'",
    )

    # Protocol
    protocol_version: str = Field(default="0.1.0")

    def to_summary(self) -> str:
        """Human-readable summary of this agent."""
        caps = ", ".join(c.get("name", "?") for c in self.capabilities)
        return (
            f"🤖 {self.name} (v{self.version})\n"
            f"   {self.description}\n"
            f"   Capabilities: {caps}\n"
            f"   Trust: {'⭐' * int(self.trust_score)} ({self.trust_score}/5.0)\n"
            f"   Status: {self.status}\n"
            f"   Requests served: {self.total_requests_served}"
        )

    def is_capable_of(self, capability_name: str) -> bool:
        """Check if this agent has a specific capability."""
        return any(c.get("name") == capability_name for c in self.capabilities)