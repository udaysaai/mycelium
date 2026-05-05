import json
import random
from pathlib import Path

# ---- utils inline ----
def save_json(path: str, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
# ---- utils end ----

DOMAINS = {
    "weather": [
        "get_current_weather",
        "get_forecast",
        "get_air_quality",
        "get_humidity",
        "get_temperature",
    ],
    "finance": [
        "get_stock_price",
        "get_crypto_price",
        "convert_currency",
        "get_market_summary",
        "get_exchange_rate",
    ],
    "translation": [
        "translate_text",
        "detect_language",
        "summarize_and_translate",
        "convert_to_hindi",
        "convert_to_marathi",
    ],
    "knowledge": [
        "wiki_summary",
        "wiki_search",
        "fact_lookup",
        "biography_lookup",
        "topic_explainer",
    ],
    "support": [
        "classify_ticket",
        "extract_issue",
        "draft_reply",
        "route_ticket",
        "detect_sentiment",
    ],
    "hiring": [
        "parse_resume",
        "score_candidate",
        "extract_skills",
        "rank_candidates",
        "generate_interview_questions",
    ],
    "legal": [
        "summarize_contract",
        "extract_clause",
        "detect_risk",
        "compliance_check",
        "liability_analysis",
    ],
    "medical": [
        "triage_symptoms",
        "extract_prescription",
        "medical_summary",
        "patient_risk_score",
        "insurance_eligibility",
    ],
}

LANGS = ["english", "hindi", "marathi", "tamil", "spanish"]
STATUSES = ["online", "online", "online", "busy"]


def make_agent(agent_num, domain, capability):
    return {
        "agent_id": f"ag_bench_{agent_num:05d}",
        "name": f"{domain.title()}Agent{agent_num}",
        "description": f"Specialized {domain} agent that can {capability.replace('_', ' ')}",
        "version": "0.2.0",
        "capabilities": [
            {
                "name": capability,
                "description": f"{capability.replace('_', ' ')} for {domain} workflows"
            }
        ],
        "tags": [domain, capability.split("_")[1] if "_" in capability else capability],
        "languages": random.sample(LANGS, k=random.randint(1, 2)),
        "trust_score": round(random.uniform(2.5, 5.0), 2),
        "status": random.choice(STATUSES),
        "total_requests_served": random.randint(0, 5000),
    }


def main():
    total = 10000
    agents = []
    i = 1

    domain_items = list(DOMAINS.items())

    while len(agents) < total:
        domain, caps = random.choice(domain_items)
        capability = random.choice(caps)
        agents.append(make_agent(i, domain, capability))
        i += 1

    save_json("benchmarks/data/synthetic/agent_cards_10k.json", agents)
    print(f"✅ Saved {len(agents)} synthetic agents")


if __name__ == "__main__":
    main()