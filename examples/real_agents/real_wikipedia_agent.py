"""
🍄 US Neural: Real Wikipedia Knowledge Agent (WikiBrain)
Live Wikipedia REST API integration for real-time semantic discovery.
Port: 8013
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

import httpx

# Ensure project root is in sys.path for direct script execution
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mycelium.core.agent import Agent

# Wikimedia requires a distinct User-Agent to prevent 403 Forbidden
WIKIPEDIA_HEADERS = {
    "User-Agent": "MyceliumProtocol/0.3.0 (https://github.com/udaysaai/mycelium; contact@usneural.ai)"
}

# 1. Initialize Agent
agent = Agent(
    agent_id="ag_demo_wiki",
    name="WikiBrain",
    description="Real knowledge and factual information lookup from Wikipedia API",
    tags=["knowledge", "wiki", "encyclopedia", "research"],
    version="0.3.0",
    endpoint="http://localhost:8013",
)


# 2. Capability: Search Wikipedia
@agent.on("wiki_search")
def search_wikipedia(query: str = "", **kwargs) -> Dict[str, Any]:
    """
    Search Wikipedia for article titles and direct URLs via OpenSearch API.
    """
    search_query = query or kwargs.get("topic") or kwargs.get("q", "")
    if not search_query:
        return {"error": "Search query is required"}

    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": search_query,
        "limit": kwargs.get("limit", 5),
        "namespace": 0,
        "format": "json",
    }

    try:
        response = httpx.get(
            url,
            params=params,
            headers=WIKIPEDIA_HEADERS,
            timeout=10.0,
            follow_redirects=True,
        )

        if response.status_code == 200:
            data = response.json()
            titles = data[1] if len(data) > 1 else []
            urls = data[3] if len(data) > 3 else []

            results = []
            for i, title in enumerate(titles):
                results.append({
                    "title": title,
                    "url": urls[i] if i < len(urls) else "",
                })

            return {
                "query": search_query,
                "results": results,
                "total_found": len(results),
                "data_source": "Wikipedia API (LIVE)",
                "is_real_data": True,
            }
        else:
            return {"error": f"Search failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": f"Wikipedia search request error: {str(e)}"}


# 3. Capability: Get Wikipedia Page Summary
@agent.on("wiki_summary")
def get_wikipedia_summary(topic: str = "", **kwargs) -> Dict[str, Any]:
    """
    Fetch clean extract summary and metadata for a specific topic.
    """
    search_topic = topic or kwargs.get("query") or kwargs.get("title", "")
    if not search_topic:
        return {"error": "Topic title is required"}

    formatted_topic = search_topic.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_topic}"

    try:
        response = httpx.get(
            url,
            headers=WIKIPEDIA_HEADERS,
            timeout=10.0,
            follow_redirects=True,
        )

        if response.status_code == 200:
            data = response.json()
            extract = data.get("extract", "")
            title = data.get("title", search_topic)
            page_url = (
                data.get("content_urls", {}).get("desktop", {}).get("page", "")
            )

            return {
                "title": title,
                "summary": extract,
                "url": page_url,
                "word_count": len(extract.split()) if extract else 0,
                "data_source": "Wikipedia REST API (LIVE)",
                "is_real_data": True,
            }
        elif response.status_code == 404:
            return {"error": f"Page '{search_topic}' not found on Wikipedia."}
        else:
            return {"error": f"Summary fetch failed with status code: {response.status_code}"}

    except Exception as e:
        return {"error": f"Wikipedia summary request error: {str(e)}"}


# 4. Standalone Runner / Server
if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception as e:
        print(f"⚠️ Registry not available: {e}")
    port = int(os.getenv("PORT", 8013))
    print(f"🧠 Starting WikiBrain on port {port}...")
    agent.serve(port=port)