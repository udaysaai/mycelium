"""
🔐 Security Layer — Agent authentication, message signing, and Enterprise Access.
"""

import os
import hashlib
import hmac
import secrets
import time
from typing import Optional

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

# ============================================================
# 1. AGENT-TO-AGENT SECURITY (Message Signing)
# ============================================================

class AgentKeyPair:
    """
    Simple API key based authentication for agents.
    
    Each agent gets:
    - agent_key (public): Used to identify the agent
    - agent_secret (private): Used to sign messages
    """
    
    @staticmethod
    def generate() -> dict:
        """Generate a new key pair for an agent."""
        agent_key = f"mk_{secrets.token_hex(16)}"
        agent_secret = f"ms_{secrets.token_hex(32)}"
        
        return {
            "agent_key": agent_key,
            "agent_secret": agent_secret,
        }
    
    @staticmethod
    def sign_message(payload: str, secret: str) -> str:
        """Sign a message payload with agent's secret."""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify a message signature."""
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

# ============================================================
# 2. RATE LIMITING (DDoS Protection)
# ============================================================

class RateLimiter:
    """
    Rate limit requests to prevent abuse.
    Each agent can make X requests per minute.
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[str, list[float]] = {}
    
    def is_allowed(self, agent_id: str) -> bool:
        """Check if agent is within rate limit."""
        now = time.time()
        
        if agent_id not in self.requests:
            self.requests[agent_id] = []
        
        # Remove old requests outside window
        self.requests[agent_id] = [
            t for t in self.requests[agent_id] 
            if now - t < self.window
        ]
        
        if len(self.requests[agent_id]) >= self.max_requests:
            return False
        
        self.requests[agent_id].append(now)
        return True
    
    def remaining(self, agent_id: str) -> int:
        """How many requests remaining in current window."""
        now = time.time()
        recent = [
            t for t in self.requests.get(agent_id, []) 
            if now - t < self.window
        ]
        return max(0, self.max_requests - len(recent))


# ============================================================
# 3. US NEURAL ENTERPRISE MOAT (Server Access Control)
# ============================================================

API_KEY_NAME = "X-Mycelium-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# To enable Enterprise Mode, set the env variable: MYCELIUM_ENTERPRISE_KEY
ENTERPRISE_API_KEY = os.getenv("MYCELIUM_ENTERPRISE_KEY", None)

async def verify_api_key(api_key_header: str = Security(api_key_header)):
    """
    US Neural Enterprise Mode Verification:
    - If no Enterprise Key is set in the environment, run in Open-Source (Free) mode.
    - If set, block all unauthorized registry and discovery requests.
    """
    # Open-Source Mode (No auth required)
    if ENTERPRISE_API_KEY is None:
        return True 
        
    # Enterprise Mode (Auth required)
    if api_key_header == ENTERPRISE_API_KEY:
        return True
        
    # Hacker / Unauthorized Access Blocked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="US Neural Enterprise Auth: Invalid or missing API Key. Access Denied.",
    )