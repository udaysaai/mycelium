"""
Agent — The core building block of Mycelium.

This is what developers interact with the most.
Create an agent, add capabilities, register it, serve requests.

Usage:
    from mycelium import Agent

    agent = Agent(
        name="Translator",
        description="Translates text between languages"
    )

    @agent.on("translate")
    def handle_translate(text: str, to: str):
        # your translation logic
        return {"translated": do_translate(text, to)}

    agent.register()
    agent.serve()
"""

from __future__ import annotations

import asyncio
import signal
import time
from typing import Any, Callable, Optional


import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mycelium.core.card import AgentCard, PricingInfo
from mycelium.core.capability import Capability, CapabilitySchema
from mycelium.core.message import Message, MessageType, StatusCode
from mycelium.core.errors import (
    CapabilityNotFoundError,
    RegistrationError,
    CommunicationError,
)

console = Console()

DEFAULT_REGISTRY = "http://localhost:8000"


class Agent:
    """
    A Mycelium AI Agent.

    Create agents that can:
    - Register on the Mycelium network
    - Be discovered by other agents
    - Receive and handle requests
    - Send requests to other agents
    - Build trust through successful interactions
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "0.1.0",
        author: Optional[str] = None,
        languages: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        pricing: Optional[PricingInfo] = None,
        registry_url: str = DEFAULT_REGISTRY,
        endpoint: Optional[str] = None,
    ):
        """
        Create a new Mycelium agent.

        Args:
            name: Human-readable name for your agent
            description: What does your agent do?
            version: Semantic version of your agent
            author: Your name or email
            languages: Languages your agent supports
            tags: Search tags for discovery
            pricing: How you charge for requests
            registry_url: URL of the Mycelium registry
            endpoint: URL where your agent receives requests
        """
        self._capabilities: dict[str, Capability] = {}
        self._handlers: dict[str, Callable] = {}
        self._registry_url = registry_url
        self._is_registered = False
        self._is_serving = False

        # Build the Agent Card
        self.card = AgentCard(
            name=name,
            description=description,
            version=version,
            author=author,
            languages=languages or ["english"],
            tags=tags or [],
            pricing=pricing or PricingInfo(),
            endpoint=endpoint,
        )

        console.print(
            f"[green]🍄 Agent '{name}' created![/green] "
            f"ID: [cyan]{self.card.agent_id}[/cyan]"
        )

    @property
    def agent_id(self) -> str:
        return self.card.agent_id

    @property
    def name(self) -> str:
        return self.card.name

    # =========================================================
    # CAPABILITY REGISTRATION
    # =========================================================

    def on(
        self,
        capability_name: str,
        description: str = "",
        input_schema: Optional[dict[str, str]] = None,
        output_schema: Optional[dict[str, str]] = None,
        tags: Optional[list[str]] = None,
    ) -> Callable:
        """
        Decorator to register a capability handler.

        Usage:
            @agent.on("translate", description="Translates text")
            def handle_translate(text: str, to: str):
                return {"translated": my_translate(text, to)}
        """

        def decorator(func: Callable) -> Callable:
            cap = Capability(
                name=capability_name,
                description=description or f"Handler for {capability_name}",
                input_schema=CapabilitySchema(
                    fields=input_schema or {},
                    required=list((input_schema or {}).keys()),
                ),
                output_schema=CapabilitySchema(
                    fields=output_schema or {},
                ),
                tags=tags or [],
            )
            cap.set_handler(func)

            self._capabilities[capability_name] = cap
            self._handlers[capability_name] = func

            # Update card
            self.card.capabilities.append(cap.to_card_dict())

            console.print(
                f"  [blue]⚡ Capability registered:[/blue] "
                f"[bold]{capability_name}[/bold] — {cap.description}"
            )

            return func

        return decorator

    def add_capability(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        input_schema: Optional[dict[str, str]] = None,
        output_schema: Optional[dict[str, str]] = None,
    ) -> None:
        """Add a capability without using the decorator."""
        cap = Capability(
            name=name,
            description=description or f"Handler for {name}",
            input_schema=CapabilitySchema(
                fields=input_schema or {},
                required=list((input_schema or {}).keys()),
            ),
            output_schema=CapabilitySchema(fields=output_schema or {}),
        )
        cap.set_handler(handler)
        self._capabilities[name] = cap
        self._handlers[name] = handler
        self.card.capabilities.append(cap.to_card_dict())

    # =========================================================
    # NETWORK OPERATIONS
    # =========================================================

    async def register_async(self) -> bool:
        """Register this agent on the Mycelium network (async)."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._registry_url}/api/v1/agents/register",
                    json=self.card.model_dump(mode="json"),
                )

                if response.status_code == 200:
                    data = response.json()
                    self._is_registered = True
                    self.card.status = "online"

                    console.print(
                        Panel(
                            f"[green]✅ Agent '{self.name}' registered on Mycelium![/green]\n"
                            f"   Agent ID: [cyan]{self.agent_id}[/cyan]\n"
                            f"   Capabilities: {len(self._capabilities)}\n"
                            f"   Registry: {self._registry_url}",
                            title="🍄 Registration Successful",
                            border_style="green",
                        )
                    )
                    return True
                else:
                    raise RegistrationError(
                        f"Registry returned {response.status_code}: {response.text}"
                    )

        except httpx.ConnectError:
            raise RegistrationError(
                f"Cannot connect to registry at {self._registry_url}. "
                f"Is the registry server running?"
            )
        except Exception as e:
            raise RegistrationError(str(e))

    def register(self) -> bool:
        """Register this agent on the Mycelium network (sync wrapper)."""
        return asyncio.run(self.register_async())

    # =========================================================
    # HANDLE INCOMING REQUESTS
    # =========================================================

    async def handle_message(self, message: Message) -> Message:
        """Process an incoming message and return a response."""
        start_time = time.time()

        # Handle ping
        if message.envelope.message_type == MessageType.PING:
            return Message.create_response(
                original=message,
                outputs={"pong": True, "agent": self.name},
                status=StatusCode.SUCCESS,
            )

        # Handle capability request
        if message.envelope.message_type == MessageType.REQUEST:
            capability_name = message.payload.get("capability")
            inputs = message.payload.get("inputs", {})

            if capability_name not in self._capabilities:
                return Message.create_error(
                    original=message,
                    error_message=f"Capability '{capability_name}' not found",
                    status=StatusCode.CAPABILITY_NOT_FOUND,
                )

            try:
                capability = self._capabilities[capability_name]
                result = await capability.execute(inputs)
                processing_time = (time.time() - start_time) * 1000

                # Update stats
                self.card.total_requests_served += 1

                return Message.create_response(
                    original=message,
                    outputs=result if isinstance(result, dict) else {"result": result},
                    status=StatusCode.SUCCESS,
                    processing_time_ms=processing_time,
                )

            except Exception as e:
                return Message.create_error(
                    original=message,
                    error_message=str(e),
                    status=StatusCode.ERROR,
                )

        return Message.create_error(
            original=message,
            error_message=f"Unknown message type: {message.envelope.message_type}",
        )

    # =========================================================
    # SEND REQUESTS TO OTHER AGENTS
    # =========================================================

    async def request_async(
        self,
        agent_id: str,
        capability: str,
        inputs: dict[str, Any],
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Send a request to another agent on the network."""
        message = Message.create_request(
            from_agent=self.agent_id,
            to_agent=agent_id,
            capability=capability,
            inputs=inputs,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self._registry_url}/api/v1/messages/send",
                    json=message.model_dump(mode="json"),
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("payload", {}).get("outputs", {})
                else:
                    raise CommunicationError(
                        self.agent_id,
                        agent_id,
                        f"Registry returned {response.status_code}",
                    )

        except httpx.ConnectError:
            raise CommunicationError(
                self.agent_id,
                agent_id,
                "Cannot connect to registry",
            )

    def request(
        self,
        agent_id: str,
        capability: str,
        inputs: dict[str, Any],
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Send a request to another agent (sync wrapper)."""
        return asyncio.run(
            self.request_async(agent_id, capability, inputs, timeout)
        )

    # =========================================================
    # SERVE (Keep agent alive and listening)
    # =========================================================

    async def _serve_async(self, host: str = "0.0.0.0", port: int = 8001):
        """Start serving requests (async)."""
        try:
            from fastapi import FastAPI
            import uvicorn
        except ImportError:
            raise ImportError(
                "FastAPI and uvicorn required for serving. "
                "Install with: pip install mycelium-ai[server]"
            )

        app = FastAPI(title=f"🍄 {self.name} — Mycelium Agent")

        @app.post("/mycelium/handle")
        async def handle_request(raw_message: dict):
            message = Message(**raw_message)
            response = await self.handle_message(message)
            return response.model_dump(mode="json")

        @app.get("/mycelium/card")
        async def get_card():
            return self.card.model_dump(mode="json")

        @app.get("/mycelium/health")
        async def health():
            return {
                "status": "healthy",
                "agent": self.name,
                "agent_id": self.agent_id,
                "capabilities": list(self._capabilities.keys()),
                "requests_served": self.card.total_requests_served,
            }

        self._is_serving = True
        self.card.status = "online"
        self.card.endpoint = f"http://{host}:{port}"

        console.print(
            Panel(
                f"[green]🍄 Agent '{self.name}' is now LIVE![/green]\n\n"
                f"   Endpoint: [cyan]http://{host}:{port}[/cyan]\n"
                f"   Capabilities: {', '.join(self._capabilities.keys())}\n"
                f"   Agent ID: {self.agent_id}\n\n"
                f"   [dim]Press Ctrl+C to stop[/dim]",
                title="🌐 Agent Serving",
                border_style="green",
            )
        )

        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    def serve(self, host: str = "0.0.0.0", port: int = 8001):
        """Start serving requests (sync wrapper)."""
        asyncio.run(self._serve_async(host, port))

    # =========================================================
    # DISPLAY
    # =========================================================

    def info(self) -> None:
        """Print agent information in a nice format."""
        table = Table(title=f"🍄 Agent: {self.name}")

        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Agent ID", self.card.agent_id)
        table.add_row("Version", self.card.version)
        table.add_row("Description", self.card.description)
        table.add_row("Status", self.card.status)
        table.add_row("Capabilities", ", ".join(self._capabilities.keys()) or "None")
        table.add_row("Languages", ", ".join(self.card.languages))
        table.add_row("Tags", ", ".join(self.card.tags) or "None")
        table.add_row("Trust Score", f"{'⭐' * int(self.card.trust_score)} ({self.card.trust_score}/5.0)")
        table.add_row("Requests Served", str(self.card.total_requests_served))
        table.add_row("Registered", "✅ Yes" if self._is_registered else "❌ No")
        table.add_row("Serving", "✅ Yes" if self._is_serving else "❌ No")

        console.print(table)

    def __repr__(self) -> str:
        caps = ", ".join(self._capabilities.keys())
        return f"Agent(name='{self.name}', capabilities=[{caps}])"