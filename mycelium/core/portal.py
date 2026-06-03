import uvicorn
from fastapi import FastAPI, Request
import requests
import threading
import time

class Portal:
    def __init__(self, registry_url="https://usaai-us-neural-registry.hf.space"):
        self.registry_url = registry_url
        self.app = FastAPI()

    def share(self, name: str, description: str, port: int = 8000):
        """The magic decorator to turn a function into a Global Agent."""
        def decorator(func):
            capability_name = func.__name__
            
            @self.app.post(f"/{capability_name}")
            async def wrapper(request: Request):
                data = await request.json()
                inputs = data.get("payload", {}).get("inputs", {})
                # Execute the original function
                result = func(**inputs)
                return {
                    "status": "success",
                    "outputs": result
                }

            # Start the background registration
            def start_portal():
                print(f"🍄 [Portal] Spinning up Agent: {name}...")
                # In a real scenario, we'd use a tunnel here. 
                # For now, we register the local endpoint.
                agent_data = {
                    "agent_id": f"agent_{int(time.time())}",
                    "name": name,
                    "description": description,
                    "capabilities": [{"name": capability_name, "description": description}],
                    "endpoint": f"http://localhost:{port}" # Ideally a public URL
                }
                try:
                    requests.post(f"{self.registry_url}/api/v1/agents/register", json=agent_data)
                    print(f"✅ [Portal] {name} is now LIVE on Mycelium Global.")
                except:
                    print("❌ [Portal] Failed to reach registry.")
                
                uvicorn.run(self.app, host="0.0.0.0", port=port)

            # Return a callable that starts the portal
            func.serve = start_portal
            return func
        return decorator

# Global instance for easy use
portal = Portal()