import sys
import re
import os
from dotenv import load_dotenv
import google.generativeai as genai
from code_processor import CodeProcessor

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Fetch API key
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please add your API key.")

# Configure Gemini API
genai.configure(api_key=GOOGLE_API_KEY)


def format_response(text):
    """
    Clean and format the response text while preserving code blocks.
    Logic unchanged – uses CodeProcessor exactly as before.
    """
    return CodeProcessor.format_response(text)


def classify_section(prompt, model):
    """
    Classify the user prompt into a section using rule-based keywords and AI fallback.
    LOGIC UNCHANGED — Only formatting and readability improved.
    """

    # Normalize prompt
    prompt_lower = prompt.lower()
    prompt_words = set(re.findall(r"\b\w+\b", prompt_lower))

    # Rule-based keyword classification
    keywords = {
        "health": {
            "health", "fitness", "exercise", "diet", "nutrition", "medical",
            "doctor", "wellness", "workout", "gym", "calories", "weight",
            "sleep", "stress", "mental", "blood", "pressure", "immune",
            "immunity", "disease", "symptoms", "treatment", "medicine",
            "hospital",
        },
        "banking": {
            "bank", "money", "finance", "investment", "credit", "loan",
            "account", "saving", "budget", "stocks", "crypto", "tax",
            "wealth", "retirement", "interest", "deposit", "withdraw",
            "balance", "transaction", "economy", "market", "portfolio",
        },
        "movies": {
            "movie", "film", "cinema", "director", "actor", "actress",
            "hollywood", "blockbuster", "genre", "review", "trailer",
            "oscars", "award", "screenplay", "production", "studio",
            "sequel", "remake", "adaptation", "casting", "plot", "character",
        },
        "music": {
            "music", "song", "artist", "band", "album", "concert",
            "genre", "lyrics", "playlist", "instrument", "melody",
            "rhythm", "tune", "track", "single", "release", "tour",
            "performance", "recording", "studio", "producer", "composer",
        },
        "general": {
            "celebrity", "trend", "social", "media", "viral", "meme",
            "influencer", "tv", "show", "reality", "entertainment",
            "gossip", "fame", "star", "icon", "buzz", "hype", "scandal",
            "news", "internet", "hashtag", "tiktok", "instagram",
            "zen", "meditation", "mindfulness", "traditional", "culture",
            "wisdom", "spirituality", "philosophy", "enlightenment",
            "karma", "yoga", "buddhism", "taoism", "harmony", "balance",
            "inner", "peace", "consciousness", "awareness", "practice",
            "ritual",
        },
    }

    # Initial scoring
    scores = {section: len(prompt_words & words) for section, words in keywords.items()}

    max_score = max(scores.values())
    candidates = [
        section for section, score in scores.items()
        if score == max_score and score > 0
    ]

    # Priority handling: prefer non-general categories
    if candidates:
        if len(candidates) == 1:
            detected_section = candidates[0]
        else:
            detected_section = candidates[0] if "general" not in candidates else candidates[1]
    else:
        detected_section = "general"

    # AI fallback classification
    if detected_section == "general" or max_score < 1:
        try:
            classification_prompt = (
                "Classify this question into one of these categories: "
                "health, banking, general, movies, music. "
                f"Question: {prompt}"
            )

            ai_response = model.generate_content(classification_prompt)
            cleaned_response = re.sub(r"[^\w\s]", "", ai_response.text.strip().lower())

            detected_section = (
                cleaned_response if cleaned_response in keywords else "general"
            )
        except:
            detected_section = "general"

    return detected_section
