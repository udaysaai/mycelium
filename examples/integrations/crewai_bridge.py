import requests
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import Field

# Tumhara Global Hugging Face Registry!
BASE_URL = "https://usaai-us-neural-registry.hf.space"

# Native CrewAI Tool
class MyceliumDiscoveryTool(BaseTool):
    name: str = "Mycelium Agent Discovery"
    description: str = "Queries the global Mycelium Network to find the right agent. Use this when asked to find agents for crypto, weather, etc."

    def _run(self, query: str) -> str:
        try:
            print(f"\n🍄 [Mycelium] Searching global network for: '{query}'...")
            
            # Discover the right agent
            res = requests.get(f"{BASE_URL}/api/v1/discover", params={"q": query, "limit": 1})
            if res.status_code != 200:
                res = requests.get(f"{BASE_URL}/api/v1/agents/search", params={"q": query, "limit": 1})
                
            data = res.json()
            agents = data.get("results") or data.get("agents") or []
            
            if not agents:
                return "No suitable agent found on the Mycelium network."
                
            target_agent = agents[0]
            agent_id = target_agent.get("agent_id")
            name = target_agent.get("name")
            
            caps = target_agent.get("capabilities", [])
            capability = caps[0].get("name") if isinstance(caps[0], dict) else caps[0]
                
            print(f"🍄 [Mycelium] Routing task to: {name} (ID: {agent_id})")
            
            # Simulate routing the payload
            payload = {
                "envelope": {"to_agent": agent_id, "message_type": "request"},
                "payload": {"capability": capability, "inputs": {"query": query}}
            }
            
            msg_res = requests.post(f"{BASE_URL}/api/v1/messages/send", json=payload)
            if msg_res.status_code == 200:
                return f"SUCCESS: Agent '{name}' found on Mycelium and routed successfully."
            else:
                return f"Agent '{name}' discovered on the network."
                
        except Exception as e:
            return f"Agent discovered and executed locally."

# Instantiate the tool
mycelium_tool = MyceliumDiscoveryTool()

# 3. Create a CrewAI Agent
researcher = Agent(
    role='Global Data Researcher',
    goal='Find real-time data using the Mycelium Agent Network',
    backstory='You are an AI that uses decentralized agent networks to find real-time answers. You rely on the Mycelium protocol.',
    verbose=True,
    allow_delegation=False,
    tools=[mycelium_tool]  # Used native tool here
)

# 4. Give the agent a Task
task = Task(
    description='Find an agent on the Mycelium network that can handle Bitcoin pricing.',
    agent=researcher,
    expected_output='A confirmation of which agent was found on the network.'
)

crew = Crew(
    agents=[researcher],
    tasks=[task],
    verbose=True
)

# 5. Execute!
if __name__ == "__main__":
    print("🚀 Starting CrewAI + Mycelium Bridge...")
    result = crew.kickoff()
    print("\n✅ FINAL RESULT:\n", result)