"""
🛡️ Trust Engine — How agents build and verify reputation

Trust is calculated from:
1. Success rate (kitne requests successfully complete kiye)
2. Response time consistency
3. Uptime (kitna time online raha)
4. Peer reviews (doosre agents ki rating)
5. Age (kitne din se network pe hai)
6. Verification level (creator verified hai?)
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class TrustRecord(BaseModel):
    """Record of one interaction for trust calculation."""
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    from_agent: str
    to_agent: str
    capability_used: str
    success: bool
    response_time_ms: float
    rating: Optional[float] = None  # 1-5 from requesting agent
    feedback: Optional[str] = None


class TrustEngine:
    """
    Calculate and manage trust scores for agents.
    
    Trust Score = weighted average of:
        - Success Rate (40%)
        - Response Consistency (20%)
        - Uptime (15%)
        - Peer Rating (15%)
        - Account Age (10%)
    """
    
    def __init__(self):
        self.records: dict[str, list[TrustRecord]] = {}
    
    def record_interaction(self, record: TrustRecord):
        """Record an agent interaction for trust calculation."""
        agent_id = record.to_agent
        if agent_id not in self.records:
            self.records[agent_id] = []
        self.records[agent_id].append(record)
    
    def calculate_trust(self, agent_id: str, 
                        registered_at: datetime) -> dict:
        """Calculate comprehensive trust score."""
        records = self.records.get(agent_id, [])
        
        if not records:
            return {
                "trust_score": 0.0,
                "level": "new",
                "breakdown": {},
                "total_interactions": 0,
            }
        
        # 1. Success Rate (40% weight)
        total = len(records)
        successes = sum(1 for r in records if r.success)
        success_rate = successes / total if total > 0 else 0
        
        # 2. Response Consistency (20% weight)
        response_times = [r.response_time_ms for r in records]
        avg_rt = sum(response_times) / len(response_times)
        
        # Lower variance = more consistent = higher score
        if len(response_times) > 1:
            variance = sum((rt - avg_rt) ** 2 
                          for rt in response_times) / len(response_times)
            consistency = max(0, 1 - (variance / (avg_rt ** 2 + 1)))
        else:
            consistency = 0.5
        
        # 3. Account Age (10% weight)
        now = datetime.now(timezone.utc)
        age_days = (now - registered_at).days
        age_score = min(1.0, age_days / 90)  # Max at 90 days
        
        # 4. Peer Rating (15% weight)
        ratings = [r.rating for r in records 
                   if r.rating is not None]
        peer_rating = (sum(ratings) / len(ratings) / 5.0 
                      if ratings else 0.5)
        
        # 5. Volume bonus (15% weight)
        volume_score = min(1.0, total / 100)  # Max at 100 interactions
        
        # Weighted calculation
        trust_score = (
            success_rate * 0.40 +
            consistency * 0.20 +
            age_score * 0.10 +
            peer_rating * 0.15 +
            volume_score * 0.15
        ) * 5.0  # Scale to 0-5
        
        trust_score = round(min(5.0, trust_score), 2)
        
        # Trust level
        if trust_score >= 4.5:
            level = "legendary"
        elif trust_score >= 3.5:
            level = "trusted"
        elif trust_score >= 2.5:
            level = "established"
        elif trust_score >= 1.0:
            level = "building"
        else:
            level = "new"
        
        return {
            "trust_score": trust_score,
            "level": level,
            "total_interactions": total,
            "success_rate": round(success_rate, 3),
            "avg_response_time_ms": round(avg_rt, 1),
            "consistency_score": round(consistency, 3),
            "peer_rating": round(peer_rating * 5, 2),
            "age_days": age_days,
            "breakdown": {
                "success_component": round(success_rate * 0.40 * 5, 2),
                "consistency_component": round(consistency * 0.20 * 5, 2),
                "age_component": round(age_score * 0.10 * 5, 2),
                "rating_component": round(peer_rating * 0.15 * 5, 2),
                "volume_component": round(volume_score * 0.15 * 5, 2),
            }
        }