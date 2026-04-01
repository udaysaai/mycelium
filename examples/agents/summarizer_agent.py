"""
📝 Summarizer Agent — Summarizes text, extracts key points
"""

from mycelium import Agent

agent = Agent(
    name="QuickSummary",
    description="Summarizes long text into key points and short summaries",
    version="1.0.0",
    tags=["summarize", "text", "notes", "extract", "tldr"],
    languages=["english"],
)


@agent.on(
    "summarize",
    description="Summarize long text into a short version",
    input_schema={"text": "string — long text to summarize", "max_sentences": "integer (default 3)"},
    output_schema={"summary": "string", "key_points": "array", "word_count_original": "number"},
)
def summarize(text: str, max_sentences: int = 3):
    """Summarize text by extracting the most important sentences."""
    import re

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    if not sentences:
        return {
            "summary": text[:200],
            "key_points": [],
            "word_count_original": len(text.split()),
        }

    # Score sentences by importance (simple heuristic)
    scored = []
    words = text.lower().split()

    # Word frequency
    word_freq = {}
    for word in words:
        word = re.sub(r'[^\w]', '', word)
        if len(word) > 3:
            word_freq[word] = word_freq.get(word, 0) + 1

    for i, sentence in enumerate(sentences):
        score = 0
        sentence_words = sentence.lower().split()

        # Frequency-based score
        for word in sentence_words:
            word = re.sub(r'[^\w]', '', word)
            score += word_freq.get(word, 0)

        # Position bonus (first and last sentences are important)
        if i == 0:
            score *= 1.5
        if i == len(sentences) - 1:
            score *= 1.2

        # Length penalty (too short = probably not important)
        if len(sentence_words) < 5:
            score *= 0.5

        scored.append((score, sentence))

    # Sort by score and take top sentences
    scored.sort(key=lambda x: x[0], reverse=True)
    top_sentences = scored[:max_sentences]

    # Re-sort by original position for readability
    top_sentences_text = [s[1] for s in top_sentences]

    # Extract key points (sentences with high scores)
    key_points = [s[1][:100] for s in scored[:5]]

    return {
        "summary": ". ".join(top_sentences_text) + ".",
        "key_points": key_points,
        "word_count_original": len(words),
        "word_count_summary": len(" ".join(top_sentences_text).split()),
        "compression_ratio": round(len(" ".join(top_sentences_text).split()) / max(len(words), 1), 2),
    }


@agent.on(
    "extract_keywords",
    description="Extract important keywords from text",
    input_schema={"text": "string"},
    output_schema={"keywords": "array of strings"},
)
def extract_keywords(text: str):
    """Extract keywords from text."""
    import re

    # Common stop words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "and",
        "but", "or", "not", "no", "if", "then", "than", "that",
        "this", "these", "those", "it", "its", "my", "your", "his",
        "her", "our", "their", "what", "which", "who", "when", "where",
        "how", "all", "each", "every", "both", "few", "more", "most",
        "some", "any", "such", "only", "very", "just", "also",
    }

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    words = [w for w in words if w not in stop_words]

    # Count frequency
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, count in sorted_words[:10]]

    return {
        "keywords": keywords,
        "total_unique_words": len(freq),
    }


if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception:
        print("⚠️  Registry not available.")
    agent.serve(port=8004)