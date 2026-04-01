"""
🔐 Security Layer — Agent authentication and message signing

Every agent gets a keypair.
Every message is signed.
Nobody can impersonate another agent.
"""

import hashlib
import hmac
import secrets
import time
from typing import Optional


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
    def verify_signature(payload: str, signature: str, 
                         secret: str) -> bool:
        """Verify a message signature."""
        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)


class RateLimiter:
    """
    Rate limit requests to prevent abuse.
    
    Each agent can make X requests per minute.
    """
    
    def __init__(self, max_requests: int = 60, 
                 window_seconds: int = 60):
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