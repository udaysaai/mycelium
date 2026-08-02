"""
🍄 US Neural: Mycelium Adapter for LangChain
Drop-in semantic routing for LangChain tools and agents.
"""

import httpx
from typing import Optional, Dict, Any, List

class MyceliumSemanticRouter:
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self._client = httpx.Client(timeout=3.0)

    def discover_tool(self, user_query: str, min_score: float = 0.15) -> Optional[Dict[str, Any]]:
        try:
            headers = {"X-Mycelium-API-Key": self.api_key} if self.api_key else {}
            response = self._client.get(
                f"{self.base_url}/agents/discover",
                params={"q": user_query, "semantic": "true", "limit": 1},
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                agents = data.get("agents", [])
                
                if agents:
                    top_agent = agents[0]
                    if top_agent.get("_similarity_score", 0.0) >= min_score:
                        return top_agent
            return None
        except Exception as e:
            print(f"🍄 [Mycelium Error] Registry unreachable: {e}")
            return None

    def route_and_execute(self, user_query: str, available_tools: List[Any]):
        best_agent_meta = self.discover_tool(user_query)
        
        if not best_agent_meta:
            return None, "No suitable tool found for your request."
            
        target_tool_name = best_agent_meta.get("name")
        similarity = best_agent_meta.get("_similarity_score", 0.0)
        
        for tool in available_tools:
            if hasattr(tool, 'name') and tool.name.lower() == target_tool_name.lower():
                return target_tool_name, similarity
                
        return target_tool_name, f"Tool '{target_tool_name}' discovered in registry but not loaded in local memory."