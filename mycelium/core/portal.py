import uvicorn
from fastapi import FastAPI, Request
import requests
from pyngrok import ngrok
import time
import threading

class Portal:
    def __init__(self, registry_url="https://usaai-us-neural-registry.hf.space"):
        self.registry_url = registry_url
        self.app = FastAPI()

    def share(self, name: str, description: str, port: int = 8000, use_tunnel: bool = True):
        """Turn a function into a Global Agent with an automatic tunnel."""
        def decorator(func):
            capability_name = func.__name__
            
            @self.app.post(f"/{capability_name}")
            async def wrapper(request: Request):
                data = await request.json()
                inputs = data.get("payload", {}).get("inputs", {})
                result = func(**inputs)
                return {"status": "success", "outputs": result}

            def start_portal():
                public_url = f"http://localhost:{port}"
                
                if use_tunnel:
                    print(f"🌐 [Portal] Opening secure tunnel...")
                    try:
                        # Create ngrok tunnel
                        tunnel = ngrok.connect(port)
                        public_url = tunnel.public_url
                        print(f"🚀 [Portal] Public URL: {public_url}")
                    except Exception as e:
                        print(f"⚠️ [Portal] Tunnel failed, falling back to localhost. Error: {e}")

                # Registering with Public URL
                agent_data = {
                    "agent_id": f"agent_{int(time.time())}",
                    "name": name,
                    "description": description,
                    "capabilities": [{"name": capability_name, "description": description}],
                    "endpoint": public_url # Global URL registered!
                }
                
                try:
                    requests.post(f"{self.registry_url}/api/v1/agents/register", json=agent_data)
                    print(f"✅ [Portal] '{name}' is GLOBAL. Discovery ID: {agent_data['agent_id']}")
                except:
                    print("❌ [Portal] Registry unreachable.")
                
                uvicorn.run(self.app, host="0.0.0.0", port=port)

            func.serve = start_portal
            return func
        return decorator

portal = Portal()