"""
GitHub Data Collector
Fetches issues from GitHub repositories safely in production
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Safe fallback for production environments (Render)
    pass


class GitHubCollector:
    """
    Collect developer sentiment signals from GitHub

    Production-safe features:
    - Optional authentication
    - Strict rate-limit handling
    - Timeout protection
    - Graceful API failure handling
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"

        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "DevPulse-AI"
        }

        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
            print("✅ GitHub API authenticated")
        else:
            print("⚠️ No GitHub token found. Using unauthenticated requests.")

    def _request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """Centralized request handler"""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=15
            )

            if response.status_code == 403:
                print("⏳ GitHub rate limit hit.")
                return None

            if response.status_code >= 400:
                print(f"❌ GitHub API error {response.status_code}")
                return None

            return response

        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return None

    def collect_issues(
        self,
        repo: str,
        days: int = 30,
        max_issues: int = 50
    ) -> List[Dict]:
        """
        Collect issues from a repository
        """

        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        url = f"{self.base_url}/repos/{repo}/issues"
        params = {
            "state": "all",
            "since": since,
            "per_page": 50,
            "page": 1
        }

        results = []

        while len(results) < max_issues:
            response = self._request(url, params)
            if not response:
                break

            data = response.json()
            if not data:
                break

            for issue in data:
                if "pull_request" in issue:
                    continue

                results.append({
                    "id": issue.get("id"),
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "body": issue.get("body") or "",
                    "state": issue.get("state"),
                    "created_at": issue.get("created_at"),
                    "comments": issue.get("comments"),
                    "author": issue.get("user", {}).get("login", "unknown"),
                    "labels": [l["name"] for l in issue.get("labels", [])]
                })

                if len(results) >= max_issues:
                    break

            params["page"] += 1
            time.sleep(1)

        print(f"✅ Collected {len(results)} issues from {repo}")
        return results


# Stable repo list
TECH_REPOS = {
    "react": "facebook/react",
    "vue": "vuejs/core",
    "angular": "angular/angular",
    "nextjs": "vercel/next.js",
    "typescript": "microsoft/TypeScript",
    "python": "python/cpython",
    "django": "django/django",
    "flask": "pallets/flask"
}
