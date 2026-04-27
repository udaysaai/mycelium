"""
🍄 Mycelium — The Networking Protocol for AI Agents
"""

__version__ = "0.2.0"
__author__ = "Uday"
__protocol_version__ = "0.1.0"

from mycelium.core.errors import (
    MyceliumError,
    AgentNotFoundError,
    CapabilityNotFoundError,
    RegistrationError,
    CommunicationError,
    TrustError,
)
from mycelium.core.capability import Capability
from mycelium.core.card import AgentCard
from mycelium.core.message import Message
from mycelium.core.agent import Agent
from mycelium.network.client import Network

__all__ = [
    "Agent",
    "AgentCard",
    "Capability",
    "Message",
    "Network",
    "MyceliumError",
    "AgentNotFoundError",
    "CapabilityNotFoundError",
    "RegistrationError",
    "CommunicationError",
    "TrustError",
]