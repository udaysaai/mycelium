"""
🧠 Semantic Search Engine for Mycelium

Agents are found by MEANING, not just keywords.

"I need temperature data" → finds WeatherAgent
"translate my text"       → finds TranslatorAgent  
"crypto prices"           → finds CryptoAgent

Uses ChromaDB + sentence-transformers locally.
No API key needed. 100% free.
"""

from __future__ import annotations

import json
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False


class SemanticSearchEngine:
    """
    Vector-based semantic search for agent discovery.
    
    Instead of keyword matching:
        "weather" → only finds agents with "weather" in name
    
    Semantic matching:
        "temperature forecast" → finds WeatherAgent
        "what's the climate"  → finds WeatherAgent
        "rain tomorrow"       → finds WeatherAgent
    """

    def __init__(self, collection_name: str = "mycelium_agents"):
        if not SEMANTIC_AVAILABLE:
            raise ImportError(
                "ChromaDB not installed. Run: "
                "pip install chromadb sentence-transformers"
            )

        # Local embedding model — no API key needed!
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"  # Small, fast, good quality
        )

        # Local ChromaDB — no server needed
        self.client = chromadb.Client(
            Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name
            )
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def _build_agent_text(self, agent: dict) -> str:
        """
        Build a rich text representation of an agent
        for embedding. More context = better search.
        """
        parts = []

        # Name
        if agent.get("name"):
            parts.append(f"Agent name: {agent['name']}")

        # Description
        if agent.get("description"):
            parts.append(f"Description: {agent['description']}")

        # Capabilities
        caps = agent.get("capabilities", [])
        if caps:
            cap_texts = []
            for cap in caps:
                cap_name = cap.get("name", "")
                cap_desc = cap.get("description", "")
                if cap_name:
                    cap_texts.append(f"{cap_name}: {cap_desc}")
            if cap_texts:
                parts.append(
                    f"Capabilities: {', '.join(cap_texts)}"
                )

        # Tags
        tags = agent.get("tags", [])
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")

        # Languages
        langs = agent.get("languages", [])
        if langs:
            parts.append(f"Languages: {', '.join(langs)}")

        return " | ".join(parts)

    def index_agent(self, agent: dict) -> None:
        """Add or update an agent in the vector index."""
        agent_id = agent.get("agent_id")
        if not agent_id:
            return

        # Build rich text for embedding
        agent_text = self._build_agent_text(agent)

        # Create embedding
        embedding = self.model.encode(
            agent_text
        ).tolist()

        # Store in ChromaDB
        try:
            self.collection.upsert(
                ids=[agent_id],
                embeddings=[embedding],
                documents=[agent_text],
                metadatas=[{
                    "agent_id": agent_id,
                    "name": agent.get("name", ""),
                    "status": agent.get("status", "offline"),
                    "trust_score": float(
                        agent.get("trust_score", 0.0)
                    ),
                }],
            )
        except Exception as e:
            print(f"⚠️ Index error for {agent_id}: {e}")

    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the index."""
        try:
            self.collection.delete(ids=[agent_id])
        except Exception:
            pass

    def search(
        self,
        query: str,
        limit: int = 10,
        min_trust: float = 0.0,
        status_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for agents by semantic meaning.
        
        Args:
            query: Natural language search query
            limit: Max results to return
            min_trust: Minimum trust score filter
            status_filter: Filter by status ("online", etc.)
        
        Returns:
            List of dicts with agent_id and similarity score
        
        Example:
            results = engine.search("I need weather data")
            # Returns WeatherAgent even if query has no 
            # exact keyword match
        """
        if not query.strip():
            return []

        # Embed the query
        query_embedding = self.model.encode(query).tolist()

        # Build where filter
        where = {}
        if min_trust > 0:
            where["trust_score"] = {"$gte": min_trust}
        if status_filter:
            where["status"] = {"$eq": status_filter}

        try:
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(limit, self.collection.count()),
                where=where if where else None,
                include=["metadatas", "distances", "documents"],
            )

            if not results or not results["ids"][0]:
                return []

            # Format results
            matches = []
            for i, agent_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                # Convert cosine distance to similarity score
                similarity = round(1 - distance, 4)

                metadata = results["metadatas"][0][i]
                matches.append({
                    "agent_id": agent_id,
                    "name": metadata.get("name", ""),
                    "similarity_score": similarity,
                    "trust_score": metadata.get(
                        "trust_score", 0.0
                    ),
                })

            # Sort by similarity (highest first)
            matches.sort(
                key=lambda x: x["similarity_score"],
                reverse=True,
            )

            return matches

        except Exception as e:
            print(f"⚠️ Search error: {e}")
            return []

    def count(self) -> int:
        """Total agents in index."""
        return self.collection.count()

    def reset(self) -> None:
        """Clear all agents from index."""
        self.client.reset()