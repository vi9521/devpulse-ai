"""
Data Processor (DEFENSIVE & CRASH-PROOF)
"""

import pandas as pd
from typing import List, Dict
import os

class DataProcessor:
    def __init__(self, cache_dir: str = "backend/data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        print("✅ DataProcessor initialized")

    def process_github_issues(self, issues: List[Dict], technology: str) -> pd.DataFrame:
        if not issues:
            return pd.DataFrame()

        df = pd.DataFrame(issues)

        df["technology"] = technology
        df["title"] = df.get("title", "")
        df["body"] = df.get("body", "")
        df["text"] = df["title"].fillna("") + " " + df["body"].fillna("")

        df["created_at"] = pd.to_datetime(df.get("created_at"), errors="coerce")
        df["date"] = df["created_at"].dt.date

        df["comments_count"] = df.get("comments_count", 0)
        df["reactions"] = df.get("reactions", 0)

        df["engagement_score"] = (
            df["comments_count"].fillna(0) * 2 +
            df["reactions"].fillna(0)
        )

        df["labels"] = df.get("labels", [[]])

        def categorize(labels):
            labels = [l.lower() for l in labels] if isinstance(labels, list) else []
            if any("bug" in l for l in labels):
                return "bug"
            if any("feature" in l or "enhancement" in l for l in labels):
                return "feature"
            return "other"

        df["category"] = df["labels"].apply(categorize)

        return df[
            ["technology", "date", "text", "category", "engagement_score", "created_at"]
        ]

    def process_stackoverflow_questions(self, questions: List[Dict], technology: str) -> pd.DataFrame:
        if not questions:
            return pd.DataFrame()

        df = pd.DataFrame(questions)

        df["technology"] = technology
        df["text"] = df["title"].fillna("") + " " + df["body"].fillna("")
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        df["date"] = df["created_at"].dt.date

        return df[
            ["technology", "date", "text", "created_at"]
        ]
