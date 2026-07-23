"""
Generate semantically distinct, task-oriented queries with non-circular
ground truth over the SUPPORTED subset of the 100k corpus.

BENCHMARK POLICY: we do NOT need to classify all 100k agents. Agents in
unsupported categories are simply excluded from query-target pools; they
remain in the indexed corpus as distractors, which makes the benchmark
HARDER, not invalid.

Uniqueness mechanism: distinct task variants x intent styles
(question / command / workflow / complaint / business / personal),
plus an ONLINE semantic filter (all-MiniLM-L6-v2) that rejects any
candidate with cosine similarity > 0.85 against any accepted query.

Output: benchmarks/data/queries_v2.json
  [{query_id, query, category, target_agent_id, relevant_agent_ids}]
"""
import json
import random
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

random.seed(42)  # reproducibility

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
AGENTS_FILE = DATA_DIR / "synthetic" / "agent_cards_100k.json"
OUTPUT_FILE = DATA_DIR / "queries_v2.json"

TARGET_QUERY_COUNT = 500
SIMILARITY_CEILING = 0.85
MODEL_NAME = "all-MiniLM-L6-v2"  # same model as production discovery

# ---------------------------------------------------------------------------
# Category derivation. Priority: tags -> capabilities -> name -> description.
# Agents matching NO category are excluded from target pools (distractors).
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "forex": ["forex", "exchange rate", "currency"],
    "weather": ["weather", "forecast", "temperature", "meteorolog"],
    "crypto": ["crypto", "bitcoin", "ethereum", "token", "blockchain price"],
    "wiki": ["wiki", "encyclopedia", "knowledge lookup", "factual"],
    "translation": ["translat", "language pair", "multilingual"],
    "summarization": ["summar", "condense", "abstract"],
    "scheduling": ["schedul", "calendar", "booking", "appointment"],
    "email": ["email", "inbox", "mail"],
    "code": ["code", "programming", "debug", "refactor"],
    "news": ["news", "headline", "current events"],
    "support": ["support", "ticket", "helpdesk", "customer service"],
    "hiring": ["hiring", "recruit", "candidate", "resume", "talent", "interview"],
    "finance": ["finance", "accounting", "invoice", "budget", "expense",
                "bookkeep", "payroll"],
    "legal": ["legal", "contract", "compliance", "law", "regulat"],
}

# ---------------------------------------------------------------------------
# TASK VARIANTS: each line is a genuinely different sub-task, phrased as a
# verb phrase in everyday vocabulary (anti-circularity by construction).
# ---------------------------------------------------------------------------
TASK_VARIANTS = {
    "forex": [
        "convert a dollar amount into euros",
        "show shoppers prices in their home money at checkout",
        "figure out what my freelance invoice in pounds is worth in rupees",
        "budget my Japan trip using today's money values",
        "warn me when the euro gets cheap against the dollar",
        "pay my remote teammates in their own countries' money",
        "compare what the big banks charge on top of the mid-market rate",
        "pull last year's dollar-to-yen history for my thesis chart",
        "estimate how much a remittance home to India loses in conversion",
        "reprice my whole product catalog for the Brazilian market",
    ],
    "weather": [
        "tell me if I need an umbrella on my walk to work",
        "decide whether my drone crew can fly this afternoon",
        "pick the driest weekend next month for an outdoor wedding",
        "warn my field engineers before a storm hits their site",
        "tell me how to dress the kids for school tomorrow",
        "check if frost will hit my tomato plants tonight",
        "plan irrigation for the farm around the next dry spell",
        "figure out if my flight out of Denver is likely to be delayed by snow",
        "compare how hot the coast gets versus the hills in June",
        "get a heads up when air quality turns bad in my city",
    ],
    "crypto": [
        "check what one bitcoin sells for at this moment",
        "track the value of my ethereum stash in real money",
        "ping me if digital coins crash overnight",
        "rank which big tokens moved the most this week",
        "work out my total wallet worth across chains",
        "spot unusual buying activity before a coin spikes",
        "log every trade I make for tax season",
        "compare fees for moving coins between exchanges",
        "follow whale wallets and tell me when they sell",
        "estimate what my mining rig earns per day after electricity",
    ],
    "wiki": [
        "get the backstory of the Eiffel Tower for a school essay",
        "explain who Ada Lovelace was and why she matters",
        "give me quick facts about the French Revolution for quiz night",
        "break down photosynthesis so a twelve year old gets it",
        "settle a dinner argument about which planet has the most moons",
        "build flashcards on world capitals for my exam",
        "trace where the word 'quarantine' comes from",
        "list the key events that led to the moon landing",
        "fact check a chain message my uncle forwarded",
        "find out what the silk road actually traded",
    ],
    "translation": [
        "say 'where is the train station' in Japanese",
        "make sense of a customer message written in Portuguese",
        "prepare my product page so German shoppers can read it",
        "turn my resume into Spanish for a Madrid job application",
        "help me reply politely to a French business email",
        "subtitle my cooking videos for a Korean audience",
        "read a Chinese ingredient label for allergy concerns",
        "let my support team answer tickets that arrive in any tongue",
        "make my wedding invitations bilingual for both families",
        "understand what my in-laws are saying in their village dialect",
    ],
    "summarization": [
        "boil a 40 page report down to one paragraph",
        "give me the gist of yesterday's meeting recording",
        "shrink this article until it fits in a tweet",
        "pull the three takeaways out of a dense PDF",
        "turn a pile of customer reviews into bullet points",
        "recap a 200 message group chat I ignored all day",
        "compress research papers into notes I can revise from",
        "give the board one slide from our quarterly numbers",
        "digest my competitor's changelog into what actually matters",
        "turn a rambling podcast episode into show notes",
    ],
    "scheduling": [
        "find a slot next week when Priya and I are both free",
        "fit my dentist visit around the daily standup",
        "nudge me before my passport expires",
        "squeeze three interviews into one afternoon",
        "protect quiet focus hours on my mornings",
        "coordinate a call across Mumbai, Berlin and San Francisco time",
        "rebook everything after my flight got cancelled",
        "rotate on-call duty fairly across my team",
        "plan the kids' activities so pickups never clash",
        "block prep time automatically before every client meeting",
    ],
    "email": [
        "draft a gentle follow up to a client who went quiet",
        "stop newsletters from burying messages that matter",
        "write a cold note to an investor I met at a demo day",
        "answer support requests automatically while I'm on holiday",
        "unsubscribe me from everything I never open",
        "chase unpaid invoices with polite reminders",
        "triage my inbox into urgent, later and ignore",
        "turn long threads into a one line status for my boss",
        "catch the tone in my drafts before I hit send angry",
        "dig out an attachment someone sent me months ago",
    ],
    "code": [
        "figure out why my Python loop dies with an index error",
        "make this slow function run faster",
        "look over my pull request for silly mistakes",
        "write unit tests around my checkout logic",
        "explain what this cryptic regex actually matches",
        "untangle a merge conflict I made worse",
        "port an old script from Python 2 without breaking it",
        "hunt down the memory leak eating my server overnight",
        "sketch a database schema for a food delivery app",
        "add decent error handling to my flaky API calls",
    ],
    "news": [
        "catch me up on what markets did while I slept",
        "brief me on today's tech headlines in two minutes",
        "watch for breaking stories about my industry",
        "tell me what people are arguing about in AI this week",
        "give me a morning digest before my commute ends",
        "track how the election coverage shifts day by day",
        "alert me when my company gets mentioned anywhere",
        "compare how different outlets covered the same story",
        "surface local stories from my neighborhood, not just national ones",
        "recap the sports results I missed over the weekend",
    ],
    "support": [
        "answer the same three questions customers ask every day",
        "route angry messages to a human before they escalate",
        "keep customers updated while their problem is being worked on",
        "spot which complaints point to the same underlying bug",
        "handle the midnight rush of help requests without waking anyone",
        "turn our FAQ into instant answers people actually find",
        "measure how happy customers are after each interaction",
        "walk a confused user through resetting their account",
        "flag the customers most likely to cancel this month",
        "summarize each customer's history before an agent picks up",
    ],
    "hiring": [
        "sort a pile of applications down to a shortlist worth reading",
        "schedule phone screens without fifteen back-and-forth messages",
        "write a job post that doesn't sound like every other one",
        "check which applicants actually have the skills they claim",
        "keep candidates warm when the process drags on",
        "compare notes from five interviewers into one clear picture",
        "find people for a role nobody is applying to",
        "make sure we ask every candidate the same fair questions",
        "draft an offer letter and handle the negotiation emails",
        "figure out why good people keep dropping out of our funnel",
    ],
    "finance": [
        "chase down which invoices are still unpaid this month",
        "sort my business receipts for tax season",
        "forecast whether we run out of cash before December",
        "reconcile the bank statement against what the books say",
        "split shared team subscriptions across department budgets",
        "flag expense claims that look padded",
        "prepare the monthly numbers my accountant keeps asking for",
        "work out what hiring two engineers does to our runway",
        "track spending against budget and yell when we drift",
        "price my consulting work so I stop undercharging",
    ],
    "legal": [
        "check a vendor agreement for clauses that could hurt us",
        "explain what this NDA actually stops me from doing",
        "keep track of which client agreements renew next quarter",
        "make sure our signup flow follows privacy rules in Europe",
        "draft simple terms of service for my small app",
        "compare two versions of an agreement and show what changed",
        "remind me of filing deadlines before regulators come asking",
        "translate the scary letter we received into plain English",
        "check if my product name steps on someone's trademark",
        "prepare the paperwork for bringing on a cofounder",
    ],
}

# ---------------------------------------------------------------------------
# INTENT-STYLE WRAPPERS: six voices; framing changes are the uniqueness
# mechanism together with distinct task variants (never slot values).
# ---------------------------------------------------------------------------
STYLE_WRAPPERS = {
    "question": [
        "how do I {task}?",
        "what's the easiest way to {task}?",
        "is there anything out there that can {task}?",
    ],
    "command": [
        "go ahead and {task} for me",
        "set something up that will {task} without me asking twice",
        "just {task}, I don't care how",
    ],
    "workflow": [
        "step two of my pipeline needs to {task} before anything else runs",
        "every night at 2am my batch job has to {task}",
        "my orchestrator needs a downstream service that can {task}",
    ],
    "complaint": [
        "I'm sick of doing this by hand -- {task} so I can stop babysitting it",
        "it breaks every single time I try to {task} myself",
        "I've burned an entire weekend trying to {task} and I give up",
    ],
    "business": [
        "our startup needs a dependable way to {task} for paying customers",
        "the ops team keeps escalating that we still can't {task}",
        "we launch next month and {task} is the last unchecked box",
    ],
    "personal": [
        "for a weekend side project I'd love to {task}",
        "purely for myself, I want something that can {task}",
        "my family keeps asking me to {task} and I'd rather automate it",
    ],
}


def derive_category(agent: dict) -> str | None:
    tags = " ".join(agent.get("tags", [])).lower()
    caps = " ".join(
        f"{c.get('name', '')} {c.get('description', '')}"
        for c in agent.get("capabilities", [])
    ).lower()
    name = agent.get("name", "").lower()
    desc = agent.get("description", "").lower()
    for source in (tags, caps, name, desc):
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in source for kw in keywords):
                return category
    return None


def build_candidates(category: str) -> list[str]:
    """Full combo space for a category: task variants x style wrappers."""
    combos = []
    for task in TASK_VARIANTS[category]:
        for style_templates in STYLE_WRAPPERS.values():
            for wrapper in style_templates:
                combos.append(wrapper.format(task=task))
    random.shuffle(combos)
    return combos


def main():
    with open(AGENTS_FILE, encoding="utf-8") as f:
        agents = json.load(f)

    by_category: dict[str, list[str]] = {}
    unsupported = 0
    for a in agents:
        cat = derive_category(a)
        if cat is None:
            unsupported += 1  # stays in corpus as a distractor; not a failure
        else:
            by_category.setdefault(cat, []).append(a["agent_id"])

    supported = len(agents) - unsupported
    # Only generate for categories that have BOTH agents and task variants.
    categories = sorted(set(by_category) & set(TASK_VARIANTS))
    skipped_cats = sorted(set(by_category) - set(TASK_VARIANTS))

    print("=== COVERAGE REPORT ===")
    print(f"total_agents:         {len(agents)}")
    print(f"supported_agents:     {supported} "
          f"({100 * supported / len(agents):.1f}%)")
    print(f"unsupported_agents:   {unsupported} (kept in corpus as distractors)")
    print(f"supported_categories: {len(categories)} -> {categories}")
    if skipped_cats:
        print(f"derived-but-no-templates (skipped): {skipped_cats}")
    for cat in categories:
        print(f"  {cat:15s} {len(by_category[cat])} agents")

    model = SentenceTransformer(MODEL_NAME)
    pools = {cat: build_candidates(cat) for cat in categories}
    cursors = {cat: 0 for cat in categories}
    rejected = {cat: 0 for cat in categories}

    accepted: list[dict] = []
    accepted_texts: set[str] = set()
    accepted_emb: list[np.ndarray] = []
    qid = 0

    # Round-robin acceptance with an ONLINE semantic filter: keep a candidate
    # only if max cosine sim vs ALL accepted queries stays <= ceiling.
    while len(accepted) < TARGET_QUERY_COUNT:
        progressed = False
        for cat in categories:
            if len(accepted) >= TARGET_QUERY_COUNT:
                break
            pool, i = pools[cat], cursors[cat]
            while i < len(pool):
                text = pool[i]
                i += 1
                if text in accepted_texts:
                    continue
                vec = model.encode([text], normalize_embeddings=True)[0]
                if accepted_emb:
                    max_sim = float(np.max(np.stack(accepted_emb) @ vec))
                    if max_sim > SIMILARITY_CEILING:
                        rejected[cat] += 1
                        continue
                accepted_texts.add(text)
                accepted_emb.append(vec)
                accepted.append({
                    "query_id": qid,
                    "query": text,
                    "category": cat,
                    "target_agent_id": random.choice(by_category[cat]),
                    "relevant_agent_ids": by_category[cat][:50],
                })
                qid += 1
                progressed = True
                break  # one acceptance per category per round (balance)
            cursors[cat] = i

        if not progressed:
            # Combo space exhausted: warn and proceed with what we have.
            # (Unblocking policy: a smaller diverse set beats a blocked run.)
            print(f"\nWARNING: combo space exhausted at {len(accepted)} queries "
                  f"(target was {TARGET_QUERY_COUNT}). Writing what we have.")
            break

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(accepted, f, indent=2, ensure_ascii=False)

    counts: dict[str, int] = {}
    for q in accepted:
        counts[q["category"]] = counts.get(q["category"], 0) + 1
    print(f"\nWrote {len(accepted)} queries -> {OUTPUT_FILE}")
    print(f"Semantic-filter rejections: {sum(rejected.values())}")
    for cat in categories:
        print(f"  {cat:15s} accepted={counts.get(cat, 0):3d}  rejected={rejected[cat]:3d}")
    print("Run fix_query_diversity.py next to verify (expect 0 pairs > 0.85).")


if __name__ == "__main__":
    main()
