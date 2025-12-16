"""
Stack Overflow Data Collector (STABLE & SAFE)
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

class StackOverflowCollector:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.stackexchange.com/2.3"
        self.site = "stackoverflow"

        print("✅ StackOverflow API initialized")
        if not api_key:
            print("⚠️ No API key (limited quota)")

    def _make_request(self, endpoint: str, params: Dict) -> Dict | None:
        params["site"] = self.site
        if self.api_key:
            params["key"] = self.api_key

        try:
            res = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=10
            )
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print("❌ StackOverflow request failed:", e)
            return None

    def collect_questions(
        self,
        tag: str,
        days: int = 30,
        max_questions: int = 50
    ) -> List[Dict]:

        print(f"\n📥 Collecting StackOverflow questions for: {tag}")

        from_date = int((datetime.now() - timedelta(days=days)).timestamp())

        params = {
            "fromdate": from_date,
            "tagged": tag,
            "sort": "creation",
            "order": "desc",
            "pagesize": 100,
            "filter": "withbody"
        }

        questions = []
        page = 1

        while len(questions) < max_questions:
            params["page"] = page
            data = self._make_request("/questions", params)

            if not data or "items" not in data:
                break

            for q in data["items"]:
                questions.append({
                    "id": q.get("question_id"),
                    "title": q.get("title", ""),
                    "body": q.get("body", ""),
                    "score": q.get("score", 0),
                    "view_count": q.get("view_count", 0),
                    "answer_count": q.get("answer_count", 0),
                    "is_answered": q.get("is_answered", False),
                    "created_at": datetime.fromtimestamp(
                        q.get("creation_date", 0)
                    ).isoformat()
                })

            if not data.get("has_more"):
                break

            page += 1
            time.sleep(0.2)

        print(f"✅ Collected {len(questions)} questions")
        return questions[:max_questions]


TECH_TAGS = {
    "react": "reactjs",
    "vue": "vue.js",
    "angular": "angular",
    "python": "python",
    "django": "django",
    "flask": "flask"
}
