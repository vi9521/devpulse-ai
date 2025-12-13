"""
DevPulse Sentiment Analyzer
Production-safe version with ML fallback

Local: Uses DistilBERT
Production (Render): Uses lightweight rule-based fallback
"""

from typing import Dict, List
import re

# -----------------------------
# SAFE IMPORTS (CRITICAL FIX)
# -----------------------------
try:
    import torch
    from transformers import pipeline
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False


class DevSentimentAnalyzer:
    """
    Sentiment analyzer with graceful degradation.

    - Local: Transformer-based ML
    - Production: Rule-based heuristic
    """

    def __init__(self):
        print("Initializing DevSentimentAnalyzer...")

        self.use_ml = TORCH_AVAILABLE

        if self.use_ml:
            try:
                self.device = 0 if torch.cuda.is_available() else -1
                self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"

                print(f"Loading ML model: {self.model_name}")
                print(f"Using device: {'GPU' if self.device == 0 else 'CPU'}")

                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.model_name,
                    device=self.device
                )

                print("✅ ML Sentiment Analyzer loaded")

            except Exception as e:
                print("⚠️ ML load failed, switching to fallback:", e)
                self.use_ml = False
                self.sentiment_pipeline = None
        else:
            print("⚠️ Torch not available — using fallback mode")
            self.sentiment_pipeline = None

        # Developer-specific patterns (USED IN BOTH MODES)
        self.frustration_keywords = [
            "bug", "broken", "crash", "error", "failed", "doesn't work",
            "garbage", "terrible", "useless", "worst", "wtf"
        ]

        self.positive_keywords = [
            "love", "amazing", "awesome", "excellent",
            "perfect", "great", "works", "helpful", "thanks"
        ]

        print("✅ Sentiment Analyzer ready (safe mode)")

    # -----------------------------
    # UTILS
    # -----------------------------
    def preprocess_text(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"`{1,3}.*?`{1,3}", "", text, flags=re.DOTALL)
        return " ".join(text.split())[:512]

    # -----------------------------
    # CORE ANALYSIS
    # -----------------------------
    def analyze(self, text: str) -> Dict:
        if not text or len(text.strip()) < 5:
            return self._neutral("Text too short")

        clean_text = self.preprocess_text(text)

        if self.use_ml and self.sentiment_pipeline:
            try:
                result = self.sentiment_pipeline(clean_text)[0]
                label = result["label"]
                score = float(result["score"])

                return {
                    "label": label,
                    "score": score,
                    "confidence": "high",
                    "mode": "ml"
                }
            except Exception as e:
                print("⚠️ ML inference failed:", e)

        # -----------------------------
        # FALLBACK MODE (RENDER SAFE)
        # -----------------------------
        text_lower = text.lower()

        if any(word in text_lower for word in self.frustration_keywords):
            return {
                "label": "FRUSTRATED",
                "score": 0.35,
                "confidence": "medium",
                "mode": "fallback"
            }

        if any(word in text_lower for word in self.positive_keywords):
            return {
                "label": "POSITIVE",
                "score": 0.85,
                "confidence": "medium",
                "mode": "fallback"
            }

        return self._neutral("No strong sentiment detected")

    # -----------------------------
    # BATCH
    # -----------------------------
    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        return [self.analyze(text) for text in texts]

    # -----------------------------
    # AGGREGATION
    # -----------------------------
    def aggregate_sentiment(self, results: List[Dict]) -> Dict:
        if not results:
            return {
                "average_score": 0.5,
                "sentiment_distribution": {},
                "dominant_sentiment": "NEUTRAL"
            }

        total = len(results)
        score_sum = sum(r["score"] for r in results)

        label_counts = {}
        for r in results:
            label_counts[r["label"]] = label_counts.get(r["label"], 0) + 1

        dominant = max(label_counts, key=label_counts.get)

        return {
            "average_score": score_sum / total,
            "sentiment_distribution": {
                k: v / total for k, v in label_counts.items()
            },
            "dominant_sentiment": dominant,
            "total_analyzed": total
        }

    def _neutral(self, reason: str) -> Dict:
        return {
            "label": "NEUTRAL",
            "score": 0.5,
            "confidence": "low",
            "reason": reason,
            "mode": "fallback"
        }
