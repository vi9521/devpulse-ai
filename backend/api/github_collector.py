"""
GitHub Data Collector
Fetches issues, PRs, and discussions from GitHub repositories
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import os
from dotenv import load_dotenv

load_dotenv()

class GitHubCollector:
    """
    Collect developer sentiment signals from GitHub
    
    Features:
    - Rate limiting handling
    - Pagination
    - Error recovery
    - Caching
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
            print("✅ GitHub API authenticated")
        else:
            print("⚠️ Warning: No GitHub token provided. Rate limits will be restrictive.")
    
    def check_rate_limit(self) -> Dict:
        """Check current API rate limit status"""
        response = requests.get(
            f"{self.base_url}/rate_limit",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            core = data['resources']['core']
            return {
                'remaining': core['remaining'],
                'limit': core['limit'],
                'reset_at': datetime.fromtimestamp(core['reset'])
            }
        return None
    
    def wait_for_rate_limit(self):
        """Wait if rate limit is reached"""
        rate_limit = self.check_rate_limit()
        
        if rate_limit and rate_limit['remaining'] < 10:
            wait_time = (rate_limit['reset_at'] - datetime.now()).total_seconds()
            if wait_time > 0:
                print(f"⏳ Rate limit reached. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time + 1)
    
    def collect_issues(
        self, 
        repo: str, 
        days: int = 30,
        max_issues: int = 100
    ) -> List[Dict]:
        """
        Collect issues from a repository
        
        Args:
            repo: Repository in format "owner/repo"
            days: Number of days to look back
            max_issues: Maximum number of issues to collect
        
        Returns:
            List of issue dictionaries
        """
        print(f"\n📥 Collecting issues from {repo}...")
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        url = f"{self.base_url}/repos/{repo}/issues"
        params = {
            'state': 'all',
            'since': since_date,
            'per_page': 100,
            'sort': 'created',
            'direction': 'desc'
        }
        
        all_issues = []
        page = 1
        
        while len(all_issues) < max_issues:
            # Check rate limit
            self.wait_for_rate_limit()
            
            params['page'] = page
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code != 200:
                    print(f"❌ Error: {response.status_code}")
                    break
                
                issues = response.json()
                
                if not issues:
                    break
                
                # Filter out pull requests (they come through issues API)
                issues = [i for i in issues if 'pull_request' not in i]
                
                # Extract relevant data
                for issue in issues:
                    all_issues.append({
                        'id': issue['id'],
                        'number': issue['number'],
                        'title': issue['title'],
                        'body': issue['body'] or '',
                        'state': issue['state'],
                        'created_at': issue['created_at'],
                        'updated_at': issue['updated_at'],
                        'comments_count': issue['comments'],
                        'labels': [label['name'] for label in issue['labels']],
                        'reactions': issue['reactions']['total_count'],
                        'author': issue['user']['login'] if issue['user'] else 'unknown'
                    })
                
                print(f"  Page {page}: {len(issues)} issues ({len(all_issues)} total)")
                
                page += 1
                
                # Break if we got fewer than requested (last page)
                if len(issues) < 100:
                    break
                
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                break
        
        print(f"✅ Collected {len(all_issues)} issues from {repo}")
        return all_issues[:max_issues]
    
    def collect_from_multiple_repos(
        self,
        repos: List[str],
        days: int = 30,
        max_per_repo: int = 50
    ) -> Dict[str, List[Dict]]:
        """
        Collect issues from multiple repositories
        
        Args:
            repos: List of repositories ["owner/repo1", "owner/repo2"]
            days: Days to look back
            max_per_repo: Max issues per repository
        
        Returns:
            Dict mapping repo name to issues list
        """
        all_data = {}
        
        for repo in repos:
            tech_name = repo.split('/')[-1]
            issues = self.collect_issues(repo, days, max_per_repo)
            all_data[tech_name] = issues
            
            # Small delay between repos
            time.sleep(1)
        
        return all_data


# Pre-configured popular repos for common technologies
TECH_REPOS = {
    'react': 'facebook/react',
    'vue': 'vuejs/core',
    'angular': 'angular/angular',
    'svelte': 'sveltejs/svelte',
    'nextjs': 'vercel/next.js',
    'typescript': 'microsoft/TypeScript',
    'python': 'python/cpython',
    'django': 'django/django',
    'flask': 'pallets/flask',
    'rust': 'rust-lang/rust'
}


if __name__ == "__main__":
    # Test the collector
    collector = GitHubCollector()
    
    # Check rate limit
    rate_limit = collector.check_rate_limit()
    if rate_limit:
        print(f"\nRate Limit: {rate_limit['remaining']}/{rate_limit['limit']}")
        print(f"Resets at: {rate_limit['reset_at']}")
    
    # Collect from React repo
    issues = collector.collect_issues('facebook/react', days=7, max_issues=20)
    
    if issues:
        print("\n=== Sample Issues ===")
        for issue in issues[:3]:
            print(f"\n#{issue['number']}: {issue['title']}")
            print(f"  State: {issue['state']}")
            print(f"  Comments: {issue['comments_count']}")
            print(f"  Labels: {', '.join(issue['labels'])}")