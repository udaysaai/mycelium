"""
🌍 Translator Agent — Example Mycelium Agent

Translates text between languages.
"""

from mycelium import Agent

agent = Agent(
    name="LinguaBot",
    description="Translates text between 10+ languages including Hindi, Tamil, and Marathi",
    version="1.0.0",
    tags=["translate", "language", "hindi", "multilingual"],
    languages=["english", "hindi", "marathi", "tamil", "telugu"],
    endpoint="http://127.0.0.1:8002",
)


# Simple mock translations (replace with real API like Google Translate)
TRANSLATIONS = {
    "hello": {"hindi": "नमस्ते", "marathi": "नमस्कार", "tamil": "வணக்கம்"},
    "thank you": {"hindi": "धन्यवाद", "marathi": "धन्यवाद", "tamil": "நன்றி"},
    "how are you": {"hindi": "आप कैसे हैं?", "marathi": "तुम्ही कसे आहात?", "tamil": "எப்படி இருக்கிறீர்கள்?"},
    "goodbye": {"hindi": "अलविदा", "marathi": "निरोप", "tamil": "போய் வருகிறேன்"},
}


@agent.on(
    "translate",
    description="Translate text from English to target language",
    input_schema={"text": "string", "to": "language name (hindi, marathi, tamil)"},
    output_schema={"translated": "string", "from": "string", "to": "string"},
)
def translate(text: str, to: str):
    """Translate text to target language."""
    text_lower = text.lower().strip()
    to_lower = to.lower().strip()

    if text_lower in TRANSLATIONS and to_lower in TRANSLATIONS[text_lower]:
        return {
            "translated": TRANSLATIONS[text_lower][to_lower],
            "from": "english",
            "to": to_lower,
            "confidence": 0.99,
        }
    else:
        return {
            "translated": f"[Translation of '{text}' to {to} — connect real API]",
            "from": "english",
            "to": to_lower,
            "confidence": 0.0,
            "note": "Mock translation — integrate Google/DeepL API for production",
        }


@agent.on(
    "detect_language",
    description="Detect the language of given text",
    input_schema={"text": "string"},
    output_schema={"language": "string", "confidence": "float"},
)
def detect_language(text: str):
    """Detect language of text."""
    # Simple mock detection
    if any(c >= "\u0900" and c <= "\u097F" for c in text):
        return {"language": "hindi", "confidence": 0.9}
    elif any(c >= "\u0B80" and c <= "\u0BFF" for c in text):
        return {"language": "tamil", "confidence": 0.9}
    else:
        return {"language": "english", "confidence": 0.8}


if __name__ == "__main__":
    agent.info()

    try:
        agent.register()
    except Exception:
        print("⚠️  Registry not available. Starting standalone.")

    agent.serve(host="127.0.0.1", port=8002)