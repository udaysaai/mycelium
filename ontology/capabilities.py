"""
🧬 Universal Capability Ontology

Standard categories and types for agent capabilities.
This is what makes cross-domain communication possible.

Like how HTTP has standard methods (GET, POST, PUT, DELETE),
Mycelium has standard capability types.
"""

CAPABILITY_ONTOLOGY = {
    
    # ============================================
    # KNOWLEDGE & INFORMATION
    # ============================================
    "knowledge": {
        "description": "Agent provides information or data",
        "subtypes": {
            "search": "Search for information",
            "lookup": "Look up specific data",
            "monitor": "Continuously monitor for changes",
            "aggregate": "Combine data from multiple sources",
            "verify": "Verify facts or claims",
        },
        "domains": [
            "weather", "news", "finance", "health", 
            "legal", "science", "geography", "history",
            "technology", "sports", "entertainment",
        ]
    },
    
    # ============================================
    # TRANSFORMATION
    # ============================================
    "transform": {
        "description": "Agent converts data from one form to another",
        "subtypes": {
            "translate": "Convert between languages",
            "summarize": "Make content shorter",
            "expand": "Make content longer/detailed",
            "convert": "Convert between formats/units",
            "extract": "Pull specific info from larger data",
            "generate": "Create new content from input",
        },
        "domains": [
            "language", "text", "code", "image", 
            "audio", "video", "data", "document",
        ]
    },
    
    # ============================================
    # ANALYSIS
    # ============================================
    "analyze": {
        "description": "Agent examines data and provides insights",
        "subtypes": {
            "sentiment": "Determine emotional tone",
            "classify": "Categorize into groups",
            "compare": "Compare two or more items",
            "predict": "Forecast future outcomes",
            "evaluate": "Assess quality or risk",
            "detect": "Find patterns or anomalies",
        },
        "domains": [
            "text", "code", "financial", "medical",
            "legal", "security", "performance", "market",
        ]
    },
    
    # ============================================
    # ACTION
    # ============================================
    "action": {
        "description": "Agent performs real-world actions",
        "subtypes": {
            "send": "Send message/email/notification",
            "book": "Make a reservation/booking",
            "buy": "Purchase something",
            "schedule": "Set up calendar events",
            "create": "Create documents/files",
            "deploy": "Deploy code/services",
        },
        "domains": [
            "email", "calendar", "payment", "travel",
            "shopping", "social_media", "cloud", "database",
        ]
    },
    
    # ============================================
    # REASONING
    # ============================================
    "reason": {
        "description": "Agent performs complex thinking",
        "subtypes": {
            "plan": "Create step-by-step plans",
            "decide": "Make decisions from options",
            "negotiate": "Find optimal agreements",
            "debate": "Argue for/against positions",
            "solve": "Solve complex problems",
            "advise": "Give expert recommendations",
        },
        "domains": [
            "business", "technical", "legal", "medical",
            "financial", "educational", "strategic", "ethical",
        ]
    },
}


class CapabilityMapper:
    """
    Maps any capability description to standard ontology.
    
    This is what enables cross-domain discovery.
    
    Example:
        mapper = CapabilityMapper()
        
        # All of these map to the SAME category:
        mapper.classify("get_weather")        → knowledge.lookup.weather
        mapper.classify("fetch_forecast")     → knowledge.lookup.weather  
        mapper.classify("weather_lookup")     → knowledge.lookup.weather
        
        # So when someone searches "I need weather data",
        # ALL three agents are found.
    """
    
    # Keyword to ontology mapping
    KEYWORD_MAP = {
        # Knowledge
        "weather": ("knowledge", "lookup", "weather"),
        "news": ("knowledge", "search", "news"),
        "stock": ("knowledge", "lookup", "finance"),
        "price": ("knowledge", "lookup", "finance"),
        
        # Transform
        "translate": ("transform", "translate", "language"),
        "summarize": ("transform", "summarize", "text"),
        "convert": ("transform", "convert", "data"),
        "generate": ("transform", "generate", "text"),
        
        # Analysis
        "review": ("analyze", "evaluate", "code"),
        "sentiment": ("analyze", "sentiment", "text"),
        "predict": ("analyze", "predict", "market"),
        "detect": ("analyze", "detect", "security"),
        
        # Action
        "email": ("action", "send", "email"),
        "book": ("action", "book", "travel"),
        "schedule": ("action", "schedule", "calendar"),
        "deploy": ("action", "deploy", "cloud"),
        
        # Reasoning
        "plan": ("reason", "plan", "business"),
        "decide": ("reason", "decide", "business"),
        "advise": ("reason", "advise", "business"),
    }
    
    @classmethod
    def classify(cls, capability_name: str, 
                 description: str = "") -> tuple:
        """Classify a capability into the ontology."""
        text = f"{capability_name} {description}".lower()
        
        best_match = None
        best_score = 0
        
        for keyword, category in cls.KEYWORD_MAP.items():
            if keyword in text:
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    best_match = category
        
        if best_match:
            return best_match
        
        return ("unknown", "unknown", "general")
    
    @classmethod
    def are_compatible(cls, cap1: str, cap2: str) -> float:
        """
        Check if two capabilities are related.
        Returns compatibility score 0.0 to 1.0
        """
        cat1 = cls.classify(cap1)
        cat2 = cls.classify(cap2)
        
        score = 0.0
        if cat1[0] == cat2[0]:  # Same category
            score += 0.5
        if cat1[1] == cat2[1]:  # Same subtype
            score += 0.3
        if cat1[2] == cat2[2]:  # Same domain
            score += 0.2
        
        return score