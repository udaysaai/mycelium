"""
📖 REAL Wikipedia Agent — Uses Wikipedia API (NO API key needed!)
Fetches real knowledge from Wikipedia.
"""

import httpx
from mycelium import Agent

agent = Agent(
    name="WikiBrain",
    description="Fetches REAL knowledge from Wikipedia — summaries, key facts, and search for any topic",
    version="1.0.0",
    tags=["wikipedia", "knowledge", "real", "search", "facts", "encyclopedia"],
    languages=["english"],
    endpoint="http://localhost:8013",     # ← YEH ADD KAR
)


@agent.on(
    "wiki_summary",
    description="Get a summary of any topic from Wikipedia",
    input_schema={"topic": "string — any topic (person, place, concept, etc.)"},
    output_schema={"title": "string", "summary": "string", "url": "string"},
)
def wiki_summary(topic: str):
    """Get Wikipedia summary for a topic."""
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + topic.replace(" ", "_")

    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)

        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", topic),
                "summary": data.get("extract", "No summary available"),
                "description": data.get("description", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "thumbnail": data.get("thumbnail", {}).get("source", ""),
                "word_count": len(data.get("extract", "").split()),
                "data_source": "Wikipedia API (LIVE)",
                "is_real_data": True,
            }
        elif response.status_code == 404:
            return {"error": f"Topic '{topic}' not found on Wikipedia", "is_real_data": False}
        else:
            return {"error": f"API error: {response.status_code}", "is_real_data": False}

    except Exception as e:
        return {"error": f"Request failed: {str(e)}", "is_real_data": False}


@agent.on(
    "wiki_search",
    description="Search Wikipedia for articles related to a query",
    input_schema={"query": "string — search query", "limit": "integer (default 5)"},
    output_schema={"results": "array of article titles"},
)
def wiki_search(query: str, limit: int = 5):
    """Search Wikipedia for articles."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": min(limit, 10),
        "format": "json",
    }

    try:
        response = httpx.get(url, params=params, timeout=10)

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
                "query": query,
                "results": results,
                "total_found": len(results),
                "data_source": "Wikipedia API (LIVE)",
                "is_real_data": True,
            }
        else:
            return {"error": f"Search failed: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception as e:
        print(f"⚠️ Registry: {e}")
    agent.serve(port=8013)