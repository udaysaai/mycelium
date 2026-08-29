"""
🍄 US Neural: Anthropic MCP (Model Context Protocol) Bridge
Hijacks MCP servers to route tools semantically via Mycelium in <10ms,
bypassing the slow LLM decision-making process.
Now with HOL (Human-On-the-Loop) Guard for mutating tools.
"""

import sys
import os
import time
import httpx
from rich.console import Console
from rich.panel import Panel
from ...security import hol_guard

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from integrations.langchain import MyceliumSemanticRouter

# Smart Import for HOL Guard (Works whether folder is 'security/' or 'mycelium/security/')
try:
    from ...security.hol_guard import HOLGuard, ToolClass, GuardDecision
except ImportError:
    # Fallback agar 'security' folder root mein hai
    from security.hol_guard import HOLGuard, ToolClass, GuardDecision

console = Console()
MYCELIUM_REGISTRY = "http://127.0.0.1:8000/api/v1/agents/register"

# ---------------------------------------------------------
# 1. Mocking an Anthropic MCP Server
# ---------------------------------------------------------
mock_mcp_server_tools = [
    {
        "name": "mcp_github_search",
        "description": "Search GitHub repositories, issues, and PRs.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}
    },
    {
        "name": "mcp_postgres_query",
        "description": "Execute read-only SQL queries on the production database.",
        "inputSchema": {"type": "object", "properties": {"sql": {"type": "string"}}}
    },
    {
        "name": "mcp_slack_notifier",
        "description": "Send alert messages to specific Slack channels.",
        "inputSchema": {"type": "object", "properties": {"channel": {"type": "string"}}}
    }
]

# ---------------------------------------------------------
# 2. HOL Guard Setup (Security Gate)
# ---------------------------------------------------------
guard = HOLGuard(require_approval=True)
guard.register_tool_class("mcp_github_search", ToolClass.READ_ONLY)
guard.register_tool_class("mcp_postgres_query", ToolClass.MUTATING)
guard.register_tool_class("mcp_slack_notifier", ToolClass.MUTATING)

# ---------------------------------------------------------
# 3. The Ingestion Engine (MCP -> Mycelium)
# ---------------------------------------------------------
def ingest_mcp_to_mycelium():
    console.print("[dim]🔄 Connecting to Anthropic MCP Server...[/dim]")
    time.sleep(0.5)
    console.print("[bold green]✅ Connected to MCP Server. Ingesting tools...[/bold green]")
    
    for tool in mock_mcp_server_tools:
        payload = {
            "agent_id": tool["name"].lower(),
            "name": tool["name"],
            "description": tool["description"],
            "tags": ["mcp", "anthropic", "tool"]
        }
        try:
            httpx.post(MYCELIUM_REGISTRY, json=payload)
            console.print(f"  🍄 Indexed MCP Tool: [cyan]{tool['name']}[/cyan] into Semantic Mesh.")
        except Exception as e:
            console.print(f"[red]Failed to index {tool['name']}: {e}[/red]")

# ---------------------------------------------------------
# 4. Execution (The Sub-10ms Route + Security Gate)
# ---------------------------------------------------------
def main():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]🤖 Anthropic MCP + 🍄 US Neural Mycelium[/bold cyan]\n"
        "[dim]Routing MCP Tools semantically without LLM latency[/dim]\n"
        "[dim]With HOL Guard security gate for mutating tools[/dim]"
    ))
    
    # Step 1: Ingest
    ingest_mcp_to_mycelium()
    time.sleep(0.5)
    
    # Step 2: Initialize Router
    router = MyceliumSemanticRouter()
    
    # Step 3: A tricky user intent (No exact keyword matches)
    user_query = "I need to find some open source code for a react dashboard."
    
    console.print(f"\n[bold magenta]User Intent:[/bold magenta] '{user_query}'")
    
    t0 = time.perf_counter()
    # Bypassing Claude completely!
    best_tool = router.discover_tool(user_query)
    latency_ms = (time.perf_counter() - t0) * 1000
    
    if best_tool:
        # ============================================
        # 🛡️ HOL GUARD GATE (Between match & invocation)
        # ============================================
        guard_result = guard.gate(
            tool_name=best_tool["name"],
            tool_description=best_tool.get("description", "")
        )
        
        if guard_result.decision == GuardDecision.DENIED:
            console.print(f"\n[bold red]🛑 BLOCKED by HOL Guard:[/bold red] {best_tool['name']}")
            console.print(f"  [dim]Reason: {guard_result.reason}[/dim]")
            console.print(f"  [dim]Tool was NEVER invoked.[/dim]")
            return
            
        if guard_result.decision == GuardDecision.PENDING_HUMAN:
            console.print(f"\n[bold yellow]⏸️  HOL Guard:[/bold yellow] {best_tool['name']} is MUTATING.")
            console.print(f"  [dim]Awaiting human approval...[/dim]")
            # For demo purposes, we simulate the human approving it automatically
            guard_result = guard.gate(
                tool_name=best_tool["name"],
                tool_description=best_tool.get("description", ""),
                human_decision=True
            )
            console.print(f"  [bold green]✅ Human approved. Proceeding...[/bold green]")

        # ============================================
        # ORIGINAL SUCCESS OUTPUT
        # ============================================
        console.print(f"\n[bold green]✅ Success! Bypassed Claude LLM Routing.[/bold green]")
        console.print(f"🎯 [bold white]Target MCP Tool:[/bold white] [bold cyan]{best_tool['name']}[/bold cyan]")
        console.print(f"📊 [bold yellow]Confidence:[/bold yellow] {best_tool.get('_similarity_score', 0.0) * 100:.1f}%")
        console.print(f"⚡ [bold red]Mycelium Latency:[/bold red] {latency_ms:.2f} ms")
        console.print(f"🛡️ [bold blue]Guard Status:[/bold blue] {guard_result.decision.value} ({guard_result.tool_class.value})")
        console.print("\n[dim]Note: Anthropic's Claude would take ~2.5 seconds and consume output tokens to make this decision.[/dim]")
    else:
        console.print("\n[bold red]❌ Routing Failed[/bold red]")

if __name__ == "__main__":
    main()