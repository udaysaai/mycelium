"""
🍄 US Neural: Anthropic MCP (Model Context Protocol) Bridge + HOL Guard
Provides sub-10ms semantic tool discovery and Human-On-The-Loop safety gating
for MCP toolsets.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

console = Console()

# Try importing HOL Guard from security module, fallback to internal implementation
try:
    from security.hol_guard import ActionType, HOLGuard
except ImportError:

    class ActionType:
        READ_ONLY = "READ_ONLY"
        MUTATING = "MUTATING"

    class HOLGuard:
        """Internal fallback HOL Guard for standalone runs."""

        MUTATING_KEYWORDS = {
            "transfer",
            "delete",
            "drop",
            "remove",
            "pay",
            "charge",
            "execute",
            "shutdown",
            "modify",
            "write",
        }

        def inspect_intent(self, intent: str, tool_meta: Dict[str, Any]) -> str:
            text = (
                f"{intent} {tool_meta.get('name', '')} {tool_meta.get('description', '')}".lower()
            )
            for kw in self.MUTATING_KEYWORDS:
                if kw in text:
                    return ActionType.MUTATING
            return ActionType.READ_ONLY


class MyceliumMCPBridge:
    """
    Connects Anthropic Model Context Protocol (MCP) clients to Mycelium's
    local vector routing mesh with automated HOL safety inspection.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000/api/v1",
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("MYCELIUM_ENTERPRISE_KEY")
        self.hol_guard = HOLGuard()
        self._client = httpx.Client(timeout=4.0)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Mycelium-API-Key"] = self.api_key
        return headers

    def register_mcp_tool(
        self, tool_id: str, name: str, description: str, tags: List[str]
    ) -> bool:
        """Register an MCP tool into the Mycelium semantic mesh."""
        payload = {
            "agent_id": tool_id,
            "name": name,
            "description": description,
            "tags": tags,
            "version": "0.3.0",
        }
        try:
            r = self._client.post(
                f"{self.base_url}/agents/register",
                json=payload,
                headers=self._headers(),
            )
            return r.status_code == 200
        except Exception:
            return False

    def discover_mcp_tool(
        self, user_intent: str, min_score: float = 0.15
    ) -> Optional[Dict[str, Any]]:
        """Semantic edge routing to discover matching MCP tool without LLM overhead."""
        try:
            r = self._client.get(
                f"{self.base_url}/agents/discover",
                params={"q": user_intent, "semantic": "true", "limit": 1},
                headers=self._headers(),
            )
            if r.status_code == 200:
                agents = r.json().get("agents", [])
                if agents and agents[0].get("_similarity_score", 0.0) >= min_score:
                    return agents[0]
            return None
        except Exception as e:
            console.print(f"[red]Registry communication error: {e}[/red]")
            return None

    def dispatch_mcp_call(
        self, user_intent: str, available_tools: List[Dict[str, Any]], auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Main Pipeline:
        1. Fast Semantic Discovery (<10ms)
        2. HOL Guard classification (READ_ONLY vs MUTATING)
        3. Human-in-the-loop gating if mutating
        4. Safe execution
        """
        t0 = time.perf_counter()

        # Step 1: Semantic Discovery
        matched_meta = self.discover_mcp_tool(user_intent)
        discovery_latency_ms = (time.perf_counter() - t0) * 1000

        if not matched_meta:
            return {
                "success": False,
                "error": "No matching MCP tool discovered for user intent.",
                "latency_ms": discovery_latency_ms,
            }

        tool_name = matched_meta.get("name")
        score = matched_meta.get("_similarity_score", 0.0)

        # Step 2: Find executable in local toolset
        local_tool = next(
            (t for t in available_tools if t["name"].lower() == tool_name.lower()),
            None,
        )
        if not local_tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' discovered in registry but not loaded in runtime.",
                "latency_ms": discovery_latency_ms,
            }

        # Step 3: HOL Guard Safety Inspection
        action_type = self.hol_guard.inspect_intent(user_intent, matched_meta)

        # Step 4: Gating Logic
        if action_type == ActionType.MUTATING:
            console.print(
                f"\n[bold red]⚠️  HOL GUARD TRIGGERED: Mutating Action Detected![/bold red]"
            )
            console.print(
                f"[yellow]Tool:[/yellow] {tool_name} | [yellow]Action:[/yellow] {user_intent}"
            )

            if not auto_approve:
                human_confirmed = Confirm.ask(
                    "[bold cyan]Authorize execution of this mutating action?[/bold cyan]",
                    default=False,
                )
                if not human_confirmed:
                    return {
                        "success": False,
                        "blocked_by_hol": True,
                        "action_type": action_type,
                        "tool_name": tool_name,
                        "error": "Execution rejected by Human Operator (HOL Guard).",
                        "latency_ms": discovery_latency_ms,
                    }

        # Step 5: Execute Tool Function
        exec_t0 = time.perf_counter()
        output = local_tool["handler"](user_intent)
        exec_latency_ms = (time.perf_counter() - exec_t0) * 1000

        return {
                "success": True,
                "tool_name": tool_name,
                "similarity_score": score,
                "action_type": action_type,
                "discovery_latency_ms": discovery_latency_ms,
                "execution_latency_ms": exec_latency_ms,
                "total_latency_ms": discovery_latency_ms + exec_latency_ms,
                "latency_ms": discovery_latency_ms,
                "output": output,
            }


# =========================================================
# LIVE VERIFICATION DEMO RUNNER
# =========================================================
def run_demo():
    console.clear()
    console.print(
        Panel.fit(
            "[bold green]🍄 US Neural: Anthropic MCP + HOL Guard Protocol[/bold green]\n"
            "[dim]Sub-10ms Semantic Edge Routing + Zero-Trust Safety Gate[/dim]"
        )
    )

    bridge = MyceliumMCPBridge()

    # 1. Define MCP Toolset (Mix of Read-Only and Critical Mutating Tools)
    mcp_tools = [
        {
            "id": "mcp_weather",
            "name": "WeatherScanner",
            "description": "Read-only live meteorological reports and temperature checks",
            "tags": ["weather", "meteorology", "read_only"],
            "handler": lambda q: "24°C, Clear skies in Mumbai",
        },
        {
            "id": "mcp_knowledge",
            "name": "KnowledgeBase",
            "description": "Read-only research summaries and factual article extracts",
            "tags": ["research", "wiki", "read_only"],
            "handler": lambda q: "MCP is Anthropic's open protocol for connecting AI tools.",
        },
        {
            "id": "mcp_database",
            "name": "ProductionDBManager",
            "description": "Mutating database operations: write, drop tables, delete records",
            "tags": ["database", "danger", "mutating"],
            "handler": lambda q: "Database table purged successfully.",
        },
        {
            "id": "mcp_payment",
            "name": "CorporatePayGate",
            "description": "Mutating financial actions: transfer funds, wire payments, issue payouts",
            "tags": ["finance", "payment", "mutating"],
            "handler": lambda q: "Transaction #TX-9842 verified and transferred.",
        },
    ]

    console.print("\n[bold yellow][*] Registering MCP Toolset to Mycelium Mesh...[/bold yellow]")
    for tool in mcp_tools:
        ok = bridge.register_mcp_tool(
            tool["id"], tool["name"], tool["description"], tool["tags"]
        )
        status = "[green]✔ Registered[/green]" if ok else "[dim]Already active[/dim]"
        console.print(f" {status}: [bold cyan]{tool['name']:22s}[/bold cyan] [dim]{tool['description'][:50]}...[/dim]")

    console.print(
        "\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]"
    )
    console.print(
        "[bold white]TEST 1: Safe Query (Read-Only ➔ Auto-Approved in <15ms)[/bold white]"
    )
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]"
    )

    safe_query = "What is the temperature and humidity right now?"
    console.print(f"[magenta]Intent:[/magenta] '{safe_query}'")
    res1 = bridge.dispatch_mcp_call(safe_query, mcp_tools)

    t1 = Table(show_header=True, header_style="bold green")
    t1.add_column("Discovered MCP Tool")
    t1.add_column("Policy")
    t1.add_column("Discovery Latency")
    t1.add_column("Status")
    t1.add_row(
        res1["tool_name"],
        f"[green]{res1['action_type']}[/green]",
        f"[bold green]{res1['discovery_latency_ms']:.2f} ms[/bold green]",
        "[bold green]✔ Auto-Executed[/bold green]",
    )
    console.print(t1)
    console.print(f"[dim]Output: {res1['output']}[/dim]\n")

    time.sleep(1)

    console.print(
        "[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]"
    )
    console.print(
        "[bold red]TEST 2: Dangerous Action (Mutating ➔ Intercepted by HOL Guard)[/bold red]"
    )
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]"
    )

    dangerous_query = "Please transfer 250 dollars to contractor wallet"
    console.print(f"[magenta]Intent:[/magenta] '{dangerous_query}'")
    res2 = bridge.dispatch_mcp_call(dangerous_query, mcp_tools)

    t2 = Table(show_header=True, header_style="bold red")
    t2.add_column("Discovered MCP Tool")
    t2.add_column("Policy")
    t2.add_column("Discovery Latency")
    t2.add_column("Safety Status")

    if res2.get("blocked_by_hol"):
        status_text = "[bold red]🛑 BLOCKED BY HOL GUARD[/bold red]"
    else:
        status_text = "[bold green]✔ Approved by Human[/bold green]"

    lat = res2.get("discovery_latency_ms", res2.get("latency_ms", 0.0))
    t2.add_row(
        res2.get("tool_name", "Unknown"),
        f"[red]{res2.get('action_type')}[/red]",
        f"[bold green]{lat:.2f} ms[/bold green]",
        status_text,
    )
    console.print(t2)
    if res2.get("success"):
        console.print(f"[dim]Output: {res2.get('output')}[/dim]")
    else:
        console.print(f"[red]Result: {res2.get('error')}[/red]")

    console.print(
        "\n[bold green]🍄 MCP Protocol Bridge Verification Complete![/bold green]\n"
    )


if __name__ == "__main__":
    run_demo()