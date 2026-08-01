import sys
import os
import time
import httpx
from rich.console import Console
from rich.panel import Panel

# Fix the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from integrations.langchain import MyceliumSemanticRouter

console = Console()

class MockLangChainTool:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def run(self, query):
        return f"Executing {self.name} logic for: {query}"

tools = [
    MockLangChainTool(name="ForexAgent", description="Convert currency and get exchange rates"),
    MockLangChainTool(name="DebuggerAgent", description="Fix code errors"),
    MockLangChainTool(name="WeatherBot", description="Get local climate info")
]

def register_tools_to_server():
    """Register our local tools to the Mycelium server so it can find them."""
    for tool in tools:
        payload = {
            "agent_id": tool.name.lower(),
            "name": tool.name,
            "description": tool.description,
            "tags": []
        }
        try:
            httpx.post("http://127.0.0.1:8000/api/v1/agents/register", json=payload)
        except Exception:
            pass

def main():
    console.clear()
    console.print(Panel.fit(
        "[bold green]🍄 US Neural - LangChain Semantic Routing Demo[/bold green]\n"
        "[dim]Bypassing LLM routing with local Vector-Mesh[/dim]"
    ))
    
    # 1. Register tools to server first
    console.print("[dim]Registering local tools to Mycelium registry...[/dim]")
    register_tools_to_server()
    time.sleep(0.5)
    
    # 2. Init Router
    router = MyceliumSemanticRouter()
    user_query = "I need to change some dollars into euros"
    
    console.print(f"\n[bold magenta]User Intent:[/bold magenta] '{user_query}'")
    console.print("[dim]Routing via Mycelium Protocol...[/dim]\n")
    
    t0 = time.perf_counter()
    tool_name, score_or_error = router.route_and_execute(user_query, tools)
    latency_ms = (time.perf_counter() - t0) * 1000
    
    if tool_name and isinstance(score_or_error, float):
        console.print(f"✅ [bold green]Successfully Routed to:[/bold green] [bold cyan]{tool_name}[/bold cyan]")
        console.print(f"📊 [bold yellow]Semantic Confidence:[/bold yellow] {score_or_error * 100:.1f}%")
        console.print(f"⚡ [bold red]Routing Latency:[/bold red] {latency_ms:.2f} ms")
        console.print("\n[dim](If we used OpenAI for this routing, it would take ~2000ms and cost tokens. We did it locally in milliseconds.)[/dim]")
    else:
        console.print(f"❌ [red]Routing Failed:[/red] {score_or_error}")

if __name__ == "__main__":
    main()