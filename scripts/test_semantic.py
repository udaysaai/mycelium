"""
🧠 Test Semantic Search v0.2.0

Tests that agents are found by MEANING, not keywords.
"""

import httpx

REGISTRY = "http://localhost:8000"

def test_semantic(query: str, expected_agent: str):
    r = httpx.get(
        f"{REGISTRY}/api/v1/agents/discover",
        params={"q": query, "semantic": True},
        timeout=15
    )
    data = r.json()
    agents = data.get("agents", [])
    names = [a.get("name", "") for a in agents]
    
    found = expected_agent in names
    icon = "✅" if found else "❌"
    
    print(f"\n{icon} Query: '{query}'")
    print(f"   Expected: {expected_agent}")
    print(f"   Got: {names[:3]}")
    print(f"   Search type: {data.get('search_type')}")
    
    return found


if __name__ == "__main__":
    print("\n🧠 MYCELIUM v0.2.0 — Semantic Search Tests\n")
    print("=" * 55)

    tests = [
        # These WON'T work with keyword search
        # But WILL work with semantic search ✨
        (
            "I need temperature data for my city",
            "RealWeather"
        ),
        (
            "What's it like outside today?",
            "RealWeather"
        ),
        (
            "Convert my text to another language",
            "RealTranslator"
        ),
        (
            "Speak Hindi please",
            "RealTranslator"
        ),
        (
            "What's the value of digital currency?",
            "CryptoTracker"
        ),
        (
            "Bitcoin Ethereum market",
            "CryptoTracker"
        ),
        (
            "Tell me about a famous person",
            "WikiBrain"
        ),
        (
            "How much does dollar cost in rupees?",
            "CurrencyMaster"
        ),
    ]

    passed = 0
    for query, expected in tests:
        if test_semantic(query, expected):
            passed += 1

    print(f"\n{'=' * 55}")
    print(f"Results: {passed}/{len(tests)} passed")

    if passed == len(tests):
        print("🟢 ALL SEMANTIC TESTS PASSED!")
        print("v0.2.0 semantic search is working! 🍄")
    elif passed > len(tests) // 2:
        print("🟡 Most tests passed!")
    else:
        print("🔴 Issues detected — check ChromaDB setup")