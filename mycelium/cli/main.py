import typer
import requests
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(help="🍄 Mycelium CLI: The Universal Agent Interface")
console = Console()
BASE_URL = "https://usaai-us-neural-registry.hf.space"

def fetch_agents_with_fallback(query: str):
    """Internal helper to find agents using Semantic Search with a local keyword fallback."""
    try:
        # Step 1: Try Semantic Search (Discovery)
        res = requests.get(f"{BASE_URL}/api/v1/discover", params={"q": query, "limit": 5}, timeout=10)
        agents = []
        if res.status_code == 200:
            agents = res.json().get("results") or res.json().get("agents") or []

        # Step 2: Fallback to Keyword Search if no results found
        if not agents:
            res_all = requests.get(f"{BASE_URL}/api/v1/agents", timeout=10)
            if res_all.status_code == 200:
                all_agents = res_all.json().get("agents", [])
                # Simple keyword matching across name, description, and capabilities
                q = query.lower()
                agents = [
                    a for a in all_agents 
                    if q in a['name'].lower() or 
                       q in a.get('description', '').lower() or 
                       any(q in str(cap).lower() for cap in a.get('capabilities', []))
                ]
        return agents
    except Exception as e:
        console.print(f"[bold red]Registry Connection Error:[/bold red] {e}")
        return []

@app.command()
def discover(q: str = typer.Argument(..., help="What kind of agent are you looking for?")):
    """🔍 Discover agents on the global Mycelium network."""
    console.print(f"\n[bold cyan]🍄 Searching Mycelium Network for:[/bold cyan] [italic]'{q}'...[/italic]")
    
    agents = fetch_agents_with_fallback(q)
    
    if not agents:
        console.print("[bold red]❌ No agents found. Try keywords like 'Weather', 'Crypto', or 'Cloud'.[/bold red]")
        return

    table = Table(title="Mycelium Global Registry", title_style="bold magenta", border_style="cyan")
    table.add_column("Agent ID", style="dim")
    table.add_column("Name", style="green")
    table.add_column("Capabilities", style="yellow")
    table.add_column("Status", justify="center")

    for agent in agents:
        # Extract capability names
        raw_caps = agent.get('capabilities', [])
        cap_names = []
        for c in raw_caps:
            if isinstance(c, dict): cap_names.append(c.get('name', 'unknown'))
            else: cap_names.append(str(c))
        
        caps_str = ", ".join(cap_names)
        status = "🟢" if agent.get('status', 'online') == 'online' else "🔴"
        
        table.add_row(
            agent.get('agent_id', 'N/A'), 
            agent.get('name', 'Unknown'), 
            caps_str, 
            status
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(agents)} agents matching your request.[/dim]")

@app.command()
def hire(capability: str, input_text: str):
    """🚀 'Hire' an agent: Finds the best agent and routes your task instantly."""
    console.print(Panel(f"Targeting: [bold green]{capability}[/bold green]\nInput: [italic]{input_text}[/italic]", title="[bold cyan]US Neural Relay[/bold cyan]"))
    
    agents = fetch_agents_with_fallback(capability)
    
    if not agents:
        console.print("[bold red]❌ No agent found to handle this task.[/bold red]")
        return

    agent = agents[0]
    agent_id = agent['agent_id']
    name = agent['name']
    
    # Get first capability name
    raw_caps = agent.get('capabilities', [])
    first_cap = "execute"
    if raw_caps:
        first_cap = raw_caps[0].get('name') if isinstance(raw_caps[0], dict) else str(raw_caps[0])

    console.print(f"🍄 [bold blue]Agent Hired:[/bold blue] {name} ([dim]{agent_id}[/dim])")
    
    # Execution (Relay via Protocol)
    payload = {
        "envelope": {"to_agent": agent_id, "message_type": "request"},
        "payload": {
            "capability": first_cap, 
            "inputs": {"query": input_text}
        }
    }
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Routing through Mycelium backbone...", total=None)
            msg_res = requests.post(f"{BASE_URL}/api/v1/messages/send", json=payload, timeout=15)
            
        if msg_res.status_code == 200:
            output = msg_res.json().get("payload", {}).get("outputs", "Success (Intent Relayed)")
            console.print(Panel(str(output), title="[bold green]Final Result[/bold green]", border_style="green"))
        else:
            console.print("[bold yellow]⚠ Request sent. Check https://mycelium-agents.netlify.app for live logs.[/bold yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Relay Error:[/bold red] {e}")

if __name__ == "__main__":
    app()