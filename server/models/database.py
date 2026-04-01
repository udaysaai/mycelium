"""
💾 Persistent Database for Mycelium Registry

Agents and their data survive server restarts.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

DB_PATH = Path("data/mycelium.db")


def get_db():
    """Get database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            version TEXT DEFAULT '0.1.0',
            author TEXT,
            capabilities TEXT DEFAULT '[]',
            endpoint TEXT,
            pricing TEXT DEFAULT '{}',
            languages TEXT DEFAULT '["english"]',
            tags TEXT DEFAULT '[]',
            trust_score REAL DEFAULT 0.0,
            total_requests_served INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            avg_response_time_ms REAL,
            registered_at TEXT,
            last_seen TEXT,
            status TEXT DEFAULT 'offline',
            protocol_version TEXT DEFAULT '0.1.0'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent TEXT,
            to_agent TEXT,
            capability TEXT,
            success BOOLEAN,
            response_time_ms REAL,
            rating REAL,
            feedback TEXT,
            timestamp TEXT,
            FOREIGN KEY (to_agent) REFERENCES agents(agent_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            from_agent TEXT,
            to_agent TEXT,
            message_type TEXT,
            capability TEXT,
            status TEXT,
            timestamp TEXT
        )
    """)
    
    conn.commit()
    conn.close()


class AgentDB:
    """Database operations for agents."""
    
    @staticmethod
    def save(agent_data: dict):
        """Save or update an agent."""
        conn = get_db()
        
        # Convert lists/dicts to JSON strings
        data = dict(agent_data)
        for key in ["capabilities", "pricing", "languages", "tags"]:
            if key in data and not isinstance(data[key], str):
                data[key] = json.dumps(data[key])
        
        conn.execute("""
            INSERT OR REPLACE INTO agents 
            (agent_id, name, description, version, author,
             capabilities, endpoint, pricing, languages, tags,
             trust_score, total_requests_served, success_rate,
             avg_response_time_ms, registered_at, last_seen, 
             status, protocol_version)
            VALUES 
            (:agent_id, :name, :description, :version, :author,
             :capabilities, :endpoint, :pricing, :languages, :tags,
             :trust_score, :total_requests_served, :success_rate,
             :avg_response_time_ms, :registered_at, :last_seen,
             :status, :protocol_version)
        """, data)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get(agent_id: str) -> Optional[dict]:
        """Get an agent by ID."""
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM agents WHERE agent_id = ?", 
            (agent_id,)
        ).fetchone()
        conn.close()
        
        if row:
            data = dict(row)
            for key in ["capabilities", "pricing", 
                        "languages", "tags"]:
                if data.get(key):
                    data[key] = json.loads(data[key])
            return data
        return None
    
    @staticmethod
    def list_all(limit: int = 50, 
                 status: Optional[str] = None) -> list[dict]:
        """List all agents."""
        conn = get_db()
        
        query = "SELECT * FROM agents"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY registered_at DESC LIMIT ?"
        params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        agents = []
        for row in rows:
            data = dict(row)
            for key in ["capabilities", "pricing", 
                        "languages", "tags"]:
                if data.get(key):
                    data[key] = json.loads(data[key])
            agents.append(data)
        
        return agents
    
    @staticmethod
    def delete(agent_id: str) -> bool:
        """Delete an agent."""
        conn = get_db()
        cursor = conn.execute(
            "DELETE FROM agents WHERE agent_id = ?", 
            (agent_id,)
        )
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def search(query: str, limit: int = 10) -> list[dict]:
        """Search agents by name or description."""
        conn = get_db()
        rows = conn.execute("""
            SELECT * FROM agents 
            WHERE name LIKE ? OR description LIKE ?
            OR tags LIKE ? OR capabilities LIKE ?
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", 
              f"%{query}%", f"%{query}%", limit)).fetchall()
        conn.close()
        
        agents = []
        for row in rows:
            data = dict(row)
            for key in ["capabilities", "pricing", 
                        "languages", "tags"]:
                if data.get(key):
                    data[key] = json.loads(data[key])
            agents.append(data)
        
        return agents
    
    @staticmethod
    def update_stats(agent_id: str, 
                     requests_served: int,
                     last_seen: str):
        """Update agent statistics."""
        conn = get_db()
        conn.execute("""
            UPDATE agents 
            SET total_requests_served = ?,
                last_seen = ?
            WHERE agent_id = ?
        """, (requests_served, last_seen, agent_id))
        conn.commit()
        conn.close()


# Initialize DB on import
init_db()