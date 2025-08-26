# app/services/sentiments.py
from __future__ import annotations
import warnings

# --- Try Hugging Face pipeline first, fallback to VADER ---
_HF_OK = True
try:
    from transformers import pipeline
    warnings.filterwarnings("ignore", message="Examining the path of torch.classes")
    _sentiment_pipe = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        device=-1,   # CPU
    )
except Exception:
    _HF_OK = False
    _sentiment_pipe = None

# VADER fallback
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon")
    _vader = SentimentIntensityAnalyzer()
except Exception:
    _vader = None


def _tone_heuristic(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["amazing", "awesome", "great", "!"]):
        return "Enthusiastic"
    if any(p in lower for p in ["please", "thank you", "thanks"]):
        return "Polite"
    if any(u in lower for u in ["urgent", "asap", "immediately"]):
        return "Urgent"
    return "Casual"


def analyze(text: str) -> dict:
    """
    Returns: { 'label': str, 'score': float, 'tone': str }
    label ∈ {'Positive','Negative','Neutral'}
    """
    label = "Neutral"
    score = 0.0

    if _HF_OK and _sentiment_pipe is not None:
        try:
            res = _sentiment_pipe(text)[0]  # {'label': 'POSITIVE', 'score': 0.99}
            raw = str(res.get("label", "")).upper()
            if "POS" in raw:
                label = "Positive"
            elif "NEG" in raw:
                label = "Negative"
            else:
                label = "Neutral"
            score = float(res.get("score", 0.0))
        except Exception:
            pass

    # Fallback to VADER if HF failed or unavailable
    if label == "Neutral" and score == 0.0 and _vader is not None:
        try:
            vs = _vader.polarity_scores(text)
            compound = float(vs.get("compound", 0.0))
            score = abs(compound)
            if compound >= 0.05:
                label = "Positive"
            elif compound <= -0.05:
                label = "Negative"
            else:
                label = "Neutral"
        except Exception:
            pass

    return {
        "label": label,
        "score": round(score, 3),
        "tone": _tone_heuristic(text),
    }
