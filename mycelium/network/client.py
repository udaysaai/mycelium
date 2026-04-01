"""
Network — The client to interact with the Mycelium network.

Use this to discover agents, search by capability, and more.

Usage:
    from mycelium import Network

    network = Network()
    agents = network.discover("I need a translator")
    result = network.request(agents[0].agent_id, "translate", {"text": "Hello"})
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
from rich.console import Console
from rich.table import Table

from mycelium.core.card import AgentCard
from mycelium.core.errors import AgentNotFoundError, CommunicationError

console = Console()

DEFAULT_REGISTRY = "http://localhost:8000"


class Network:
    """
    Client for the Mycelium network.

    Discover agents, send requests, and interact with the ecosystem.
    """

    def __init__(self, registry_url: str = DEFAULT_REGISTRY):
        self._registry_url = registry_url

    async def discover_async(
        self,
        query: str,
        capability: Optional[str] = None,
        tags: Optional[list[str]] = None,
        min_trust: float = 0.0,
        limit: int = 10,
    ) -> list[AgentCard]:
        """
        Discover agents on the network.

        Args:
            query: Natural language search ("I need a translator")
            capability: Specific capability name to search for
            tags: Filter by tags
            min_trust: Minimum trust score (0-5)
            limit: Maximum number of results

        Returns:
            List of matching AgentCards
        """
        params = {
            "q": query,
            "limit": limit,
            "min_trust": min_trust,
        }
        if capability:
            params["capability"] = capability
        if tags:
            params["tags"] = ",".join(tags)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self._registry_url}/api/v1/agents/discover",
                    params=params,
                )

                if response.status_code == 200:
                    data = response.json()
                    agents = [AgentCard(**agent) for agent in data.get("agents", [])]

                    if agents:
                        console.print(
                            f"[green]🔍 Found {len(agents)} agents "
                            f"for: '{query}'[/green]"
                        )
                    else:
                        console.print(
                            f"[yellow]🔍 No agents found for: '{query}'[/yellow]"
                        )

                    return agents
                else:
                    return []

        except httpx.ConnectError:
            console.print(
                f"[red]❌ Cannot connect to registry at "
                f"{self._registry_url}[/red]"
            )
            return []

    def discover(
        self,
        query: str,
        capability: Optional[str] = None,
        tags: Optional[list[str]] = None,
        min_trust: float = 0.0,
        limit: int = 10,
    ) -> list[AgentCard]:
        """Discover agents (sync wrapper)."""
        import asyncio
        return asyncio.run(
            self.discover_async(query, capability, tags, min_trust, limit)
        )

    async def get_agent_async(self, agent_id: str) -> AgentCard:
        """Get a specific agent's card by ID."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._registry_url}/api/v1/agents/{agent_id}"
                )

                if response.status_code == 200:
                    return AgentCard(**response.json())
                elif response.status_code == 404:
                    raise AgentNotFoundError(agent_id)
                else:
                    raise CommunicationError(
                        "network", agent_id,
                        f"Registry error: {response.status_code}"
                    )

        except httpx.ConnectError:
            raise CommunicationError(
                "network", agent_id,
                "Cannot connect to registry"
            )

    def get_agent(self, agent_id: str) -> AgentCard:
        """Get a specific agent's card (sync wrapper)."""
        import asyncio
        return asyncio.run(self.get_agent_async(agent_id))

    async def request_async(
        self,
        agent_id: str,
        capability: str,
        inputs: dict[str, Any],
        from_agent: str = "anonymous",
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Send a request to an agent through the network."""
        from mycelium.core.message import Message

        message = Message.create_request(
            from_agent=from_agent,
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
                        from_agent, agent_id,
                        f"Request failed: {response.status_code}"
                    )

        except httpx.ConnectError:
            raise CommunicationError(
                from_agent, agent_id,
                "Cannot connect to registry"
            )

    def request(
        self,
        agent_id: str,
        capability: str,
        inputs: dict[str, Any],
        from_agent: str = "anonymous",
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Send a request to an agent (sync wrapper)."""
        import asyncio
        return asyncio.run(
            self.request_async(agent_id, capability, inputs, from_agent, timeout)
        )

    async def list_agents_async(self, limit: int = 50) -> list[AgentCard]:
        """List all agents on the network."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._registry_url}/api/v1/agents",
                    params={"limit": limit},
                )

                if response.status_code == 200:
                    data = response.json()
                    return [AgentCard(**a) for a in data.get("agents", [])]
                return []

        except httpx.ConnectError:
            console.print("[red]❌ Cannot connect to registry[/red]")
            return []

    def list_agents(self, limit: int = 50) -> list[AgentCard]:
        """List all agents (sync wrapper)."""
        import asyncio
        return asyncio.run(self.list_agents_async(limit))

    def show_agents(self, limit: int = 20) -> None:
        """Pretty print all agents on the network."""
        agents = self.list_agents(limit)

        if not agents:
            console.print("[yellow]No agents found on the network.[/yellow]")
            return

        table = Table(title="🍄 Mycelium Network — Active Agents")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("ID", style="dim")
        table.add_column("Capabilities", style="green")
        table.add_column("Trust", style="yellow")
        table.add_column("Status", style="white")
        table.add_column("Requests", justify="right")

        for agent in agents:
            caps = ", ".join(
                c.get("name", "?") for c in agent.capabilities[:3]
            )
            if len(agent.capabilities) > 3:
                caps += f" +{len(agent.capabilities) - 3}"

            status_emoji = {
                "online": "🟢",
                "offline": "🔴",
                "busy": "🟡",
            }.get(agent.status, "⚪")

            table.add_row(
                agent.name,
                agent.agent_id[:15] + "...",
                caps,
                f"{'⭐' * int(agent.trust_score)} {agent.trust_score}",
                f"{status_emoji} {agent.status}",
                str(agent.total_requests_served),
            )

        console.print(table)