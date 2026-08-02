"""
🍄 US Neural: Multi-Agent Workflow Chain
Demonstrating autonomous tool chaining via Mycelium Semantic Discovery.
"""

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

# ---------------------------------------------------------
# 1. Mock Enterprise Tools (The Workers)
# ---------------------------------------------------------
class MockTool:
    def __init__(self, name, description, response_logic):
        self.name = name
        self.description = description
        self.response_logic = response_logic

    def run(self, context):
        return self.response_logic(context)

# Logic for our tools
def weather_logic(query): 
    return "22°C, Partly Cloudy in Paris"

def translate_logic(context): 
    return f"Traduit en Français: {context.replace('22°C, Partly Cloudy in Paris', '22°C, Partiellement nuageux à Paris')}"

tools = [
    MockTool("WeatherBot", "Get real-time meteorological conditions and climate forecasts", weather_logic),
    MockTool("TranslatorAgent", "Convert and translate text from English to French accurately", translate_logic),
    MockTool("DebuggerAgent", "Fix python code errors", lambda q: "Fixed line 42")
]

# ---------------------------------------------------------
# 2. The Chain Orchestrator
# ---------------------------------------------------------
def run_autonomous_chain():
    console.clear()
    console.print(Panel.fit(
        "[bold green]🍄 US Neural - Autonomous Multi-Agent Chain[/bold green]\n"
        "[dim]Mycelium discovering and chaining tools on the fly[/dim]"
    ))
    
    # Register required tools to Mycelium server
    console.print("[dim]Registering required tools to Mycelium registry...[/dim]")
    for t in tools:
        try:
            httpx.post("http://127.0.0.1:8000/api/v1/agents/register", json={
                "agent_id": t.name.lower(),
                "name": t.name,
                "description": t.description,
                "tags": []
            })
        except Exception:
            pass
    time.sleep(0.5)

    router = MyceliumSemanticRouter()
    
    # The Complex User Request
    user_request = "Find out the climate in Paris today and say it to me in French."
    console.print(f"\n[bold magenta]Complex User Request:[/bold magenta] '{user_request}'\n")
    
    # STEP 1: Discovery & Execution 1
    step1_intent = "Find out the climate in Paris today"
    console.print(f"👉 [bold cyan]Step 1 Intent:[/bold cyan] '{step1_intent}'")
    
    t0 = time.perf_counter()
    tool1_name, score1 = router.route_and_execute(step1_intent, tools)
    
    if isinstance(score1, float):
        tool1 = next(t for t in tools if t.name == tool1_name)
        step1_output = tool1.run(step1_intent)
        console.print(f"   [green]✔ Routed to:[/green] {tool1_name} (Confidence: {score1*100:.1f}%)")
        console.print(f"   [yellow]Output 1:[/yellow] {step1_output}\n")
    else:
        console.print(f"   [red]Step 1 Failed:[/red] {score1}")
        return

    # STEP 2: Discovery & Execution 2
    step2_intent = f"translate this to french: {step1_output}"
    console.print(f"👉 [bold cyan]Step 2 Intent:[/bold cyan] '{step2_intent}'")
    
    tool2_name, score2 = router.route_and_execute(step2_intent, tools)
    
    if isinstance(score2, float):
        tool2 = next(t for t in tools if t.name == tool2_name)
        final_output = tool2.run(step1_output)
        console.print(f"   [green]✔ Routed to:[/green] {tool2_name} (Confidence: {score2*100:.1f}%)")
        console.print(f"   [bold yellow]Final Chained Output:[/bold yellow] [bold white]{final_output}[/bold white]\n")
    else:
        console.print(f"   [red]Step 2 Failed:[/red] {score2}")
        return

    total_latency = (time.perf_counter() - t0) * 1000
    console.print(f"⚡ [bold red]Total Autonomous Chain Latency:[/bold red] {total_latency:.2f} ms")
    console.print("[dim]Two distinct tools discovered and executed sequentially without hardcoded links.[/dim]\n")

if __name__ == "__main__":
    run_autonomous_chain()