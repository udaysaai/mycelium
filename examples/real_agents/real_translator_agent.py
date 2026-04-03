"""
🌍 REAL Translator Agent — Uses MyMemory Translation API
Translates text between ANY languages using real translation service.
"""

import httpx
from mycelium import Agent

agent = Agent(
    name="RealTranslator",
    description="Translates text between 50+ languages using MyMemory Translation API — REAL translations",
    version="1.0.0",
    tags=["translate", "real", "language", "hindi", "multilingual", "mymemory"],
    languages=["english", "hindi", "marathi", "spanish", "french", "german", "japanese"],
    endpoint="http://localhost:8011",     # ← YEH ADD KAR
)

# Language code mapping
LANG_CODES = {
    "hindi": "hi",
    "marathi": "mr",
    "tamil": "ta",
    "telugu": "te",
    "bengali": "bn",
    "gujarati": "gu",
    "kannada": "kn",
    "malayalam": "ml",
    "punjabi": "pa",
    "urdu": "ur",
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "japanese": "ja",
    "chinese": "zh",
    "korean": "ko",
    "arabic": "ar",
    "russian": "ru",
    "portuguese": "pt",
    "italian": "it",
}


@agent.on(
    "translate_real",
    description="Translate text between any two languages using REAL MyMemory API",
    input_schema={
        "text": "string — text to translate",
        "from_lang": "string — source language (default: english)",
        "to_lang": "string — target language name (hindi, spanish, etc.)",
    },
    output_schema={
        "translated_text": "string",
        "from_language": "string",
        "to_language": "string",
        "data_source": "string",
    },
)
def translate_real(text: str, to_lang: str, from_lang: str = "english"):
    """Translate using MyMemory API."""
    from_code = LANG_CODES.get(from_lang.lower(), from_lang.lower())
    to_code = LANG_CODES.get(to_lang.lower(), to_lang.lower())

    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": f"{from_code}|{to_code}",
    }

    try:
        response = httpx.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            translated = data["responseData"]["translatedText"]
            match_quality = data["responseData"].get("match", 0)

            return {
                "original_text": text,
                "translated_text": translated,
                "from_language": from_lang,
                "to_language": to_lang,
                "from_code": from_code,
                "to_code": to_code,
                "quality_score": round(match_quality, 2),
                "data_source": "MyMemory Translation API (LIVE)",
                "is_real_data": True,
            }
        else:
            return {"error": f"API error: {response.status_code}", "is_real_data": False}

    except Exception as e:
        return {"error": f"Translation failed: {str(e)}", "is_real_data": False}


@agent.on(
    "supported_languages",
    description="List all supported languages",
    input_schema={},
    output_schema={"languages": "array of supported language names"},
)
def supported_languages():
    return {
        "languages": list(LANG_CODES.keys()),
        "total": len(LANG_CODES),
    }


if __name__ == "__main__":
    agent.info()
    try:
        agent.register()
    except Exception as e:
        print(f"⚠️ Registry: {e}")
    agent.serve(port=8011)