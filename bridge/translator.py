"""
🌉 Agent Bridge — Cross-domain translation layer

When a Military agent talks to a Finance agent,
they speak different "languages" (different data formats,
different terminology, different schemas).

The Bridge translates between them automatically.

Military: {"threat_level": "high", "region": "south_asia"}
    ↓ [Bridge translates]
Finance:  {"risk_score": 0.85, "market": "emerging_asia"}
"""

from typing import Any


class AgentBridge:
    """
    Translates between different agent domains automatically.
    
    Example:
        bridge = AgentBridge()
        
        # Military agent sends data
        military_data = {
            "threat_level": "high",
            "confidence": 0.9,
            "region": "south_asia"
        }
        
        # Bridge translates for finance agent
        finance_data = bridge.translate(
            data=military_data,
            from_domain="military",
            to_domain="finance"
        )
        # Result: {"risk_score": 0.85, "market": "emerging_asia", ...}
    """
    
    # Domain-specific term mappings
    TERM_MAPPINGS = {
        ("military", "finance"): {
            "threat_level": "risk_score",
            "high": 0.85,
            "medium": 0.50,
            "low": 0.15,
            "region": "market",
            "south_asia": "emerging_asia",
            "casualties": "losses",
            "deployment": "allocation",
            "intelligence": "market_research",
            "strategy": "investment_strategy",
        },
        ("finance", "military"): {
            "risk_score": "threat_level",
            "market": "region",
            "portfolio": "resources",
            "investment": "deployment",
            "returns": "gains",
            "losses": "casualties",
            "bull_market": "favorable_conditions",
            "bear_market": "hostile_conditions",
        },
        ("medical", "finance"): {
            "diagnosis": "assessment",
            "treatment_cost": "expense",
            "prognosis": "forecast",
            "patient_risk": "risk_score",
            "critical": 0.95,
            "stable": 0.30,
            "recovery_time": "time_to_maturity",
        },
        ("legal", "finance"): {
            "liability": "risk_exposure",
            "settlement": "payout",
            "compliance": "regulatory_requirement",
            "verdict": "outcome",
            "damages": "losses",
            "contract_value": "deal_value",
        },
        ("technical", "business"): {
            "latency": "response_time",
            "throughput": "capacity",
            "downtime": "service_disruption",
            "bug": "issue",
            "deployment": "launch",
            "tech_debt": "operational_risk",
            "scalability": "growth_capacity",
        },
    }
    
    # Universal schema — common fields every domain understands
    UNIVERSAL_SCHEMA = {
        "confidence": "float (0-1)",
        "timestamp": "ISO 8601 datetime",
        "priority": "string (critical/high/medium/low)",
        "summary": "string (human readable)",
        "source": "string (where data came from)",
        "data": "dict (domain-specific payload)",
    }
    
    @classmethod
    def translate(cls, data: dict, from_domain: str, 
                  to_domain: str) -> dict:
        """Translate data between domains."""
        key = (from_domain.lower(), to_domain.lower())
        
        if key not in cls.TERM_MAPPINGS:
            # No direct mapping — wrap in universal schema
            return {
                "source_domain": from_domain,
                "translated": False,
                "raw_data": data,
                "summary": f"Data from {from_domain} domain (no direct translation available)",
                "confidence": 0.5,
            }
        
        mapping = cls.TERM_MAPPINGS[key]
        translated = {}
        
        for orig_key, orig_value in data.items():
            # Translate key
            new_key = mapping.get(orig_key, orig_key)
            
            # Translate value if mapping exists
            if isinstance(orig_value, str) and orig_value in mapping:
                new_value = mapping[orig_value]
            else:
                new_value = orig_value
            
            translated[new_key] = new_value
        
        translated["_translation_meta"] = {
            "from_domain": from_domain,
            "to_domain": to_domain,
            "confidence": 0.85,
            "translated_fields": len(translated) - 1,
        }
        
        return translated
    
    @classmethod
    def to_universal(cls, data: dict, domain: str) -> dict:
        """
        Convert domain-specific data to universal format.
        
        Any agent can understand universal format.
        Like English is universal language for humans.
        """
        return {
            "domain": domain,
            "confidence": data.get("confidence", 0.8),
            "priority": cls._extract_priority(data),
            "summary": cls._generate_summary(data, domain),
            "source": domain,
            "data": data,
            "universal_format_version": "0.1.0",
        }
    
    @classmethod
    def _extract_priority(cls, data: dict) -> str:
        """Extract priority from any data format."""
        for key in ["priority", "urgency", "severity", 
                     "threat_level", "risk_score", "importance"]:
            if key in data:
                val = data[key]
                if isinstance(val, str):
                    return val.lower()
                elif isinstance(val, (int, float)):
                    if val > 0.8: return "critical"
                    elif val > 0.6: return "high"
                    elif val > 0.3: return "medium"
                    else: return "low"
        return "medium"
    
    @classmethod
    def _generate_summary(cls, data: dict, domain: str) -> str:
        """Generate human-readable summary."""
        key_values = [f"{k}: {v}" for k, v in data.items() 
                      if not k.startswith("_")][:5]
        return f"[{domain}] " + ", ".join(key_values)