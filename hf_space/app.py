import os
from mycelium.server.app import app

# Hugging Face runs on port 7860 by default
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)