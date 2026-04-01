"""Custom exceptions for Mycelium."""


class MyceliumError(Exception):
    """Base exception for all Mycelium errors."""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AgentNotFoundError(MyceliumError):
    """Raised when an agent cannot be found on the network."""

    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent '{agent_id}' not found on the network.",
            code="AGENT_NOT_FOUND",
        )


class CapabilityNotFoundError(MyceliumError):
    """Raised when a requested capability doesn't exist on an agent."""

    def __init__(self, capability: str, agent_name: str):
        super().__init__(
            message=f"Capability '{capability}' not found on agent '{agent_name}'.",
            code="CAPABILITY_NOT_FOUND",
        )


class RegistrationError(MyceliumError):
    """Raised when agent registration fails."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Registration failed: {reason}",
            code="REGISTRATION_FAILED",
        )


class CommunicationError(MyceliumError):
    """Raised when agent-to-agent communication fails."""

    def __init__(self, from_agent: str, to_agent: str, reason: str):
        super().__init__(
            message=f"Communication failed from '{from_agent}' to '{to_agent}': {reason}",
            code="COMMUNICATION_FAILED",
        )


class TrustError(MyceliumError):
    """Raised when trust verification fails."""

    def __init__(self, agent_id: str, reason: str):
        super().__init__(
            message=f"Trust verification failed for '{agent_id}': {reason}",
            code="TRUST_FAILED",
        )


class TimeoutError(MyceliumError):
    """Raised when an agent request times out."""

    def __init__(self, agent_id: str, timeout: int):
        super().__init__(
            message=f"Request to agent '{agent_id}' timed out after {timeout}s.",
            code="TIMEOUT",
        )