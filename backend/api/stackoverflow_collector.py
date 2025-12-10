"""
Stack Overflow Data Collector
Fetches questions and answers from Stack Overflow API
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import gzip
from io import BytesIO

class StackOverflowCollector:
    """
    Collect developer questions from Stack Overflow
    
    API: Stack Exchange API v2.3
    Rate Limit: 300 requests/day without key, 10,000 with key
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.stackexchange.com/2.3"
        self.site = "stackoverflow"
        
        print("✅ StackOverflow API initialized")
        if not api_key:
            print("⚠️ Warning: No API key. Limited to 300 requests/day")
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make API request with error handling"""
        params['site'] = self.site
        if self.api_key:
            params['key'] = self.api_key
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=10
            )
            
            # Handle compressed response
            if response.headers.get('Content-Encoding') == 'gzip':
                content = gzip.decompress(response.content)
                data = eval(content.decode('utf-8'))  # API returns compressed JSON
            else:
                data = response.json()
            
            # Check for errors
            if 'error_id' in data:
                print(f"❌ API Error: {data.get('error_message', 'Unknown error')}")
                return None
            
            # Check quota
            if 'quota_remaining' in data:
                if data['quota_remaining'] < 10:
                    print(f"⚠️ Low quota: {data['quota_remaining']} requests remaining")
            
            return data
            
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def collect_questions(
        self,
        tag: str,
        days: int = 30,
        max_questions: int = 100
    ) -> List[Dict]:
        """
        Collect questions for a specific tag
        
        Args:
            tag: Technology tag (e.g., 'reactjs', 'python', 'django')
            days: Days to look back
            max_questions: Maximum questions to collect
        
        Returns:
            List of question dictionaries
        """
        print(f"\n📥 Collecting StackOverflow questions for tag: {tag}")
        
        from_date = int((datetime.now() - timedelta(days=days)).timestamp())
        to_date = int(datetime.now().timestamp())
        
        params = {
            'fromdate': from_date,
            'todate': to_date,
            'tagged': tag,
            'sort': 'creation',
            'order': 'desc',
            'pagesize': 100,
            'filter': 'withbody'  # Include question body
        }
        
        all_questions = []
        page = 1
        
        while len(all_questions) < max_questions:
            params['page'] = page
            
            data = self._make_request('/questions', params)
            
            if not data or 'items' not in data:
                break
            
            questions = data['items']
            
            if not questions:
                break
            
            # Extract relevant data
            for q in questions:
                all_questions.append({
                    'id': q['question_id'],
                    'title': q['title'],
                    'body': q.get('body', ''),
                    'score': q['score'],
                    'view_count': q['view_count'],
                    'answer_count': q['answer_count'],
                    'is_answered': q['is_answered'],
                    'created_at': datetime.fromtimestamp(q['creation_date']).isoformat(),
                    'tags': q['tags'],
                    'owner': q.get('owner', {}).get('display_name', 'anonymous')
                })
            
            print(f"  Page {page}: {len(questions)} questions ({len(all_questions)} total)")
            
            page += 1
            
            # Respect rate limiting
            if not data.get('has_more', False):
                break
            
            time.sleep(0.1)  # Small delay between requests
        
        print(f"✅ Collected {len(all_questions)} questions for {tag}")
        return all_questions[:max_questions]
    
    def collect_from_multiple_tags(
        self,
        tags: List[str],
        days: int = 30,
        max_per_tag: int = 50
    ) -> Dict[str, List[Dict]]:
        """
        Collect questions from multiple tags
        
        Args:
            tags: List of tags ['python', 'django', 'flask']
            days: Days to look back
            max_per_tag: Max questions per tag
        
        Returns:
            Dict mapping tag to questions list
        """
        all_data = {}
        
        for tag in tags:
            questions = self.collect_questions(tag, days, max_per_tag)
            all_data[tag] = questions
            
            # Delay between tags to respect rate limits
            time.sleep(0.5)
        
        return all_data


# Tag mappings for common technologies
TECH_TAGS = {
    'react': 'reactjs',
    'vue': 'vue.js',
    'angular': 'angular',
    'svelte': 'svelte',
    'nextjs': 'next.js',
    'typescript': 'typescript',
    'python': 'python',
    'django': 'django',
    'flask': 'flask',
    'rust': 'rust'
}


if __name__ == "__main__":
    # Test the collector
    collector = StackOverflowCollector()
    
    # Collect React questions
    questions = collector.collect_questions('reactjs', days=7, max_questions=20)
    
    if questions:
        print("\n=== Sample Questions ===")
        for q in questions[:3]:
            print(f"\nQ: {q['title']}")
            print(f"  Score: {q['score']} | Answers: {q['answer_count']} | Views: {q['view_count']}")
            print(f"  Tags: {', '.join(q['tags'])}")