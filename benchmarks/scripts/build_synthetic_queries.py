import random
import json
import random
from pathlib import Path

def save_json(path: str, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

QUERY_BANK = {
    "weather": [
        "I need temperature data for my city",
        "what's the weather outside today",
        "do I need an umbrella in mumbai",
        "show me tomorrow's forecast",
        "air quality in delhi please",
    ],
    "finance": [
        "what is the bitcoin price now",
        "convert dollar to rupees",
        "show me stock market summary",
        "what is ethereum worth",
        "exchange rate usd to inr",
    ],
    "translation": [
        "translate this text to hindi",
        "convert this sentence into marathi",
        "what language is this",
        "summarize and translate",
        "speak hindi please",
    ],
    "knowledge": [
        "tell me about a famous person",
        "search wikipedia for ai",
        "explain quantum computing",
        "give me a quick summary of india",
        "find facts about elon musk",
    ],
    "support": [
        "classify this customer complaint",
        "route this ticket to the right team",
        "draft a support reply",
        "detect the sentiment of this message",
        "extract the issue from this email",
    ],
    "hiring": [
        "parse this resume",
        "score this candidate for backend role",
        "extract skills from cv",
        "rank these candidates",
        "generate interview questions",
    ],
    "legal": [
        "summarize this contract",
        "extract liability clause",
        "check compliance risk",
        "what is the risk in this agreement",
        "find key legal clauses",
    ],
    "medical": [
        "triage these symptoms",
        "summarize patient note",
        "check patient risk score",
        "extract prescription details",
        "is this covered by insurance",
    ],
}


def main():
    queries = []
    total = 1000

    domain_names = list(QUERY_BANK.keys())

    for i in range(total):
        domain = random.choice(domain_names)
        query = random.choice(QUERY_BANK[domain])

        queries.append({
            "query_id": f"q_{i:05d}",
            "query": query,
            "expected_domain": domain,
        })

    save_json("benchmarks/data/synthetic/queries_1k.json", queries)
    print(f"✅ Saved {len(queries)} synthetic queries")


if __name__ == "__main__":
    main()