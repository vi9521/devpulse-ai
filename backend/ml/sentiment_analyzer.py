import os
import re
from typing import Dict, List

class DevSentimentAnalyzer:
    """
    Production-safe sentiment analyzer.
    ML model is lazy-loaded to avoid OOM on small instances.
    """

    def __init__(self):
        self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        self.pipeline = None
        self.ml_enabled = os.getenv("ENABLE_ML", "false").lower() == "true"

        print("Initializing DevSentimentAnalyzer...")
        print(f"ML enabled: {self.ml_enabled}")

    def _load_model(self):
        """Load ML model lazily"""
        if self.pipeline is not None:
            return

        if not self.ml_enabled:
            raise RuntimeError("ML disabled by configuration")

        try:
            from transformers import pipeline
            import torch

            device = -1  # force CPU
            print("Loading ML model lazily...")
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=device
            )
            print("✅ ML model loaded")

        except Exception as e:
            print(f"❌ ML load failed: {e}")
            self.pipeline = None
            raise

    def preprocess_text(self, text: str) -> str:
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"`[^`]*`", "", text)
        return " ".join(text.split())[:256]

    def analyze(self, text: str) -> Dict:
        if not text or len(text.strip()) < 5:
            return {"label": "NEUTRAL", "score": 0.5}

        clean_text = self.preprocess_text(text)

        # 🔁 Try ML if enabled
        if self.ml_enabled:
            try:
                self._load_model()
                result = self.pipeline(clean_text)[0]
                return {
                    "label": result["label"],
                    "score": result["score"],
                    "source": "ml"
                }
            except Exception:
                pass  # fallback below

        # 🛟 RULE-BASED FALLBACK (always safe)
        text_lower = clean_text.lower()

        if any(w in text_lower for w in ["bug", "broken", "crash", "wtf", "error"]):
            return {"label": "NEGATIVE", "score": 0.85, "source": "rules"}

        if any(w in text_lower for w in ["love", "great", "awesome", "thanks"]):
            return {"label": "POSITIVE", "score": 0.85, "source": "rules"}

        return {"label": "NEUTRAL", "score": 0.5, "source": "rules"}
