"""
Sentiment Analysis for financial news.

Uses a lightweight rule-based approach by default.
For production, swap in a FinBERT or similar transformer.
"""
import re
import pandas as pd
import numpy as np
from typing import Dict, List
from alphaedge.logger import log


# Simple financial lexicon for rule-based scoring (using prefixes)
_POSITIVE = (
    "surge", "rally", "gain", "profit", "bull", "upgrade", "beat",
    "record", "growth", "strong", "optim", "outperform", "buy",
    "boom", "soar", "jump", "positiv", "recover", "dividend",
)
_NEGATIVE = (
    "crash", "fall", "loss", "bear", "downgrade", "miss", "declin",
    "weak", "cut", "sell", "plunge", "drop", "negativ", "recession",
    "default", "risk", "correct", "slump", "layoff", "warn", "plummet"
)

class SentimentAnalyzer:
    """Analyze sentiment of financial headlines / articles."""

    def __init__(self, use_finbert: bool = False):
        self.use_finbert = use_finbert
        self._model = None
        if use_finbert:
            self._load_finbert()

    # ── Public API ───────────────────────────────────────────────
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Score a single piece of text.

        Returns:
            {"positive": float, "negative": float, "neutral": float, "compound": float}
        """
        if self.use_finbert and self._model is not None:
            return self._finbert_score(text)
        return self._lexicon_score(text)

    def analyze_batch(self, texts: List[str]) -> pd.DataFrame:
        """Score a list of texts and return a DataFrame."""
        results = [self.analyze(t) for t in texts]
        return pd.DataFrame(results)

    def get_aggregate_sentiment(self, texts: List[str]) -> float:
        """Return a single [-1, 1] aggregate sentiment for a list of texts."""
        if not texts:
            return 0.0
        scores = self.analyze_batch(texts)
        return float(scores["compound"].mean())

    # ── Lexicon scorer ───────────────────────────────────────────
    @staticmethod
    def _lexicon_score(text: str) -> Dict[str, float]:
        words = set(re.findall(r"[a-z]+", text.lower()))
        pos = sum(1 for w in words if any(w.startswith(p) for p in _POSITIVE))
        neg = sum(1 for w in words if any(w.startswith(n) for n in _NEGATIVE))
        total = pos + neg or 1
        compound = (pos - neg) / total
        return {
            "positive": pos / total,
            "negative": neg / total,
            "neutral": 1.0 - (pos + neg) / max(len(words), 1),
            "compound": compound,
        }

    # ── FinBERT (optional) ───────────────────────────────────────
    def _load_finbert(self):
        """Attempt to load FinBERT. Falls back to lexicon if unavailable."""
        try:
            from transformers import pipeline

            self._model = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                top_k=None,
            )
            log.info("FinBERT loaded successfully")
        except ImportError:
            log.warning("transformers not installed – using lexicon fallback")
            self.use_finbert = False
        except Exception as e:
            log.warning(f"FinBERT load failed ({e}) – using lexicon fallback")
            self.use_finbert = False

    def _finbert_score(self, text: str) -> Dict[str, float]:
        """Score with FinBERT."""
        try:
            results = self._model(text[:512])[0]  # type: ignore[index]
            mapping = {r["label"].lower(): r["score"] for r in results}
            pos = mapping.get("positive", 0.0)
            neg = mapping.get("negative", 0.0)
            neu = mapping.get("neutral", 0.0)
            return {
                "positive": pos,
                "negative": neg,
                "neutral": neu,
                "compound": pos - neg,
            }
        except Exception:
            return self._lexicon_score(text)
