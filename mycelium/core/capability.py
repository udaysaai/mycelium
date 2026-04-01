"""
Capability — What an agent CAN DO.

Each agent has one or more capabilities. 
Think of these as "skills" that other agents can request.
"""

from __future__ import annotations

from typing import Any, Callable, Optional
from pydantic import BaseModel, Field


class CapabilitySchema(BaseModel):
    """Schema definition for capability inputs/outputs."""

    fields: dict[str, str] = Field(
        default_factory=dict,
        description="Field name → type description mapping",
    )
    required: list[str] = Field(
        default_factory=list,
        description="Required field names",
    )
    example: Optional[dict[str, Any]] = None


class Capability(BaseModel):
    """
    A single capability of an agent.

    Example:
        cap = Capability(
            name="translate",
            description="Translates text between languages",
            input_schema=CapabilitySchema(
                fields={"text": "string", "to": "language code"},
                required=["text", "to"],
                example={"text": "Hello", "to": "hi"}
            ),
            output_schema=CapabilitySchema(
                fields={"translated": "string", "confidence": "float"},
                example={"translated": "नमस्ते", "confidence": 0.98}
            )
        )
    """

    name: str = Field(..., description="Unique capability name")
    description: str = Field(..., description="What this capability does")
    input_schema: CapabilitySchema = Field(
        default_factory=CapabilitySchema,
        description="Expected input format",
    )
    output_schema: CapabilitySchema = Field(
        default_factory=CapabilitySchema,
        description="Expected output format",
    )
    tags: list[str] = Field(default_factory=list)
    version: str = Field(default="1.0.0")
    is_async: bool = Field(default=False, description="Whether this capability runs async")
    avg_response_time_ms: Optional[float] = Field(
        default=None,
        description="Average response time in milliseconds",
    )
    cost_per_request: Optional[float] = Field(
        default=None,
        description="Cost per request in USD",
    )

    # Internal — not serialized to network
    _handler: Optional[Callable] = None

    class Config:
        arbitrary_types_allowed = True

    def set_handler(self, handler: Callable) -> None:
        """Attach a handler function to this capability."""
        self._handler = handler

    async def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute this capability with given inputs."""
        if self._handler is None:
            raise ValueError(f"No handler registered for capability '{self.name}'")

        # Validate required fields
        for field in self.input_schema.required:
            if field not in inputs:
                raise ValueError(
                    f"Missing required field '{field}' for capability '{self.name}'"
                )

        import asyncio

        if asyncio.iscoroutinefunction(self._handler):
            return await self._handler(**inputs)
        else:
            return self._handler(**inputs)

    def to_card_dict(self) -> dict:
        """Export capability info for the Agent Card (no handler)."""
        return self.model_dump(exclude={"_handler"})