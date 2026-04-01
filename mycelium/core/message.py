"""
Message — The communication format between agents.

Every agent-to-agent interaction follows this format.
Think of it as the "envelope" that carries the "letter".
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class MessageType(str, Enum):
    """Types of messages agents can send."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake_ack"


class StatusCode(str, Enum):
    """Status codes for responses."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    BUSY = "busy"
    CAPABILITY_NOT_FOUND = "capability_not_found"
    UNAUTHORIZED = "unauthorized"


class Envelope(BaseModel):
    """Message metadata — who, when, what type."""

    message_id: str = Field(
        default_factory=lambda: f"msg_{uuid.uuid4().hex[:16]}"
    )
    in_reply_to: Optional[str] = Field(
        default=None,
        description="Message ID this is replying to",
    )
    from_agent: str = Field(..., description="Sender agent ID")
    to_agent: str = Field(..., description="Receiver agent ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    protocol_version: str = Field(default="0.1.0")
    message_type: MessageType = Field(default=MessageType.REQUEST)


class RequestPayload(BaseModel):
    """Payload for REQUEST messages."""

    capability: str = Field(..., description="Which capability to invoke")
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters for the capability",
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Constraints like max_time, max_cost",
    )


class ResponsePayload(BaseModel):
    """Payload for RESPONSE messages."""

    status: StatusCode = Field(default=StatusCode.SUCCESS)
    capability: str = Field(..., description="Which capability was invoked")
    outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Output data from the capability",
    )
    error_message: Optional[str] = Field(default=None)


class MessageMeta(BaseModel):
    """Metadata about the processing."""

    processing_time_ms: Optional[float] = None
    cost_charged: Optional[float] = None
    confidence: Optional[float] = None
    retries: int = 0


class Message(BaseModel):
    """
    Complete message between two agents.

    Usage:
        # Create a request
        msg = Message.create_request(
            from_agent="ag_abc",
            to_agent="ag_xyz",
            capability="translate",
            inputs={"text": "Hello", "to": "hindi"}
        )

        # Create a response
        reply = Message.create_response(
            original=msg,
            outputs={"translated": "नमस्ते"}
        )
    """

    envelope: Envelope
    payload: dict[str, Any] = Field(default_factory=dict)
    meta: MessageMeta = Field(default_factory=MessageMeta)
    auth: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def create_request(
        cls,
        from_agent: str,
        to_agent: str,
        capability: str,
        inputs: dict[str, Any],
        constraints: Optional[dict[str, Any]] = None,
    ) -> Message:
        """Create a new request message."""
        return cls(
            envelope=Envelope(
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=MessageType.REQUEST,
            ),
            payload={
                "capability": capability,
                "inputs": inputs,
                "constraints": constraints or {},
            },
        )

    @classmethod
    def create_response(
        cls,
        original: Message,
        outputs: dict[str, Any],
        status: StatusCode = StatusCode.SUCCESS,
        processing_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> Message:
        """Create a response to a request message."""
        return cls(
            envelope=Envelope(
                from_agent=original.envelope.to_agent,
                to_agent=original.envelope.from_agent,
                message_type=MessageType.RESPONSE,
                in_reply_to=original.envelope.message_id,
            ),
            payload={
                "status": status.value,
                "capability": original.payload.get("capability", "unknown"),
                "outputs": outputs,
                "error_message": error_message,
            },
            meta=MessageMeta(processing_time_ms=processing_time_ms),
        )

    @classmethod
    def create_error(
        cls,
        original: Message,
        error_message: str,
        status: StatusCode = StatusCode.ERROR,
    ) -> Message:
        """Create an error response."""
        return cls.create_response(
            original=original,
            outputs={},
            status=status,
            error_message=error_message,
        )
    
    @classmethod
    def create_ping(cls, from_agent: str, to_agent: str) -> Message:
        """Create a ping message to check if agent is alive."""
        return cls(
            envelope=Envelope(
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=MessageType.PING,
            ),
            payload={"ping": True},
        )