import typer
import requests

app = typer.Typer()
BASE_URL = "https://usaai-us-neural-registry.hf.space"

@app.command()
def hire(query: str, data: str = ""):
    """Hire an agent from the global Mycelium network to do a task."""
    typer.echo(f"🍄 Searching Mycelium for: '{query}'...")
    
    # 1. Discovery
    res = requests.get(f"{BASE_URL}/api/v1/discover", params={"q": query, "limit": 1})
    agents = res.json().get("results", [])
    
    if not agents:
        typer.echo("❌ No agents found for this task.")
        return

    agent = agents[0]
    typer.echo(f"✅ Found Agent: {agent['name']} ({agent['agent_id']})")
    
    # 2. Execution logic (Requesting)
    # ... (yahan requests.post wala logic aayega)
    typer.echo(f"🚀 Task routed to {agent['name']}...")
    typer.echo(f"📦 Result: [Mock Result for {query}]")

if __name__ == "__main__":
    app()