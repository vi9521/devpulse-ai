"""
Data Processor
Combines data from multiple sources and prepares it for ML analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import json
import os

class DataProcessor:
    """
    Central data processing pipeline
    
    Combines data from:
    - GitHub issues
    - Stack Overflow questions
    
    Prepares for:
    - Sentiment analysis
    - Trend prediction
    - Insight generation
    """
    
    def __init__(self, cache_dir: str = 'backend/data/cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        print("✅ DataProcessor initialized")
    
    def process_github_issues(self, issues: List[Dict], technology: str) -> pd.DataFrame:
        """
        Process GitHub issues into structured format
        
        Args:
            issues: List of issue dicts from GitHub API
            technology: Technology name
        
        Returns:
            DataFrame with processed data
        """
        if not issues:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(issues)
        
        # Add technology column
        df['technology'] = technology
        
        # Combine title and body for analysis
        df['text'] = df['title'] + ' ' + df['body'].fillna('')
        
        # Parse dates
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        # Calculate engagement score
        df['engagement_score'] = (
            df['comments_count'] * 2 + 
            df['reactions']
        )
        
        # Categorize by labels
        def categorize_issue(labels):
            labels_lower = [l.lower() for l in labels]
            if any('bug' in l for l in labels_lower):
                return 'bug'
            elif any('feature' in l or 'enhancement' in l for l in labels_lower):
                return 'feature'
            elif any('question' in l or 'help' in l for l in labels_lower):
                return 'question'
            else:
                return 'other'
        
        df['category'] = df['labels'].apply(categorize_issue)
        
        return df[['technology', 'date', 'text', 'state', 'category', 
                   'comments_count', 'engagement_score', 'created_at']]
    
    def process_stackoverflow_questions(
        self, 
        questions: List[Dict], 
        technology: str
    ) -> pd.DataFrame:
        """Process Stack Overflow questions"""
        if not questions:
            return pd.DataFrame()
        
        df = pd.DataFrame(questions)
        
        df['technology'] = technology
        df['text'] = df['title'] + ' ' + df['body'].fillna('')
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        # Calculate difficulty (unanswered + low score = difficult)
        df['difficulty'] = (~df['is_answered']).astype(int) * 2 + (df['score'] < 0).astype(int)
        
        return df[['technology', 'date', 'text', 'score', 'answer_count', 
                   'view_count', 'difficulty', 'created_at']]
    
    def combine_sources(
        self,
        github_data: Dict[str, List[Dict]],
        stackoverflow_data: Dict[str, List[Dict]]
    ) -> pd.DataFrame:
        """
        Combine data from multiple sources
        
        Args:
            github_data: Dict of {technology: issues}
            stackoverflow_data: Dict of {technology: questions}
        
        Returns:
            Combined DataFrame
        """
        print("\n🔄 Combining data sources...")
        
        all_dfs = []
        
        # Process GitHub data
        for tech, issues in github_data.items():
            df = self.process_github_issues(issues, tech)
            if not df.empty:
                df['source'] = 'github'
                all_dfs.append(df)
        
        # Process StackOverflow data
        for tech, questions in stackoverflow_data.items():
            df = self.process_stackoverflow_questions(questions, tech)
            if not df.empty:
                df['source'] = 'stackoverflow'
                all_dfs.append(df)
        
        if not all_dfs:
            print("⚠️ No data to combine")
            return pd.DataFrame()
        
        # Combine all data
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        print(f"✅ Combined {len(combined_df)} records from {len(all_dfs)} sources")
        
        return combined_df
    
    def aggregate_daily_metrics(
        self,
        df: pd.DataFrame,
        sentiment_results: List[Dict]
    ) -> pd.DataFrame:
        """
        Aggregate data by date for time-series analysis
        
        Args:
            df: Combined data DataFrame
            sentiment_results: Results from sentiment analysis
        
        Returns:
            Daily aggregated metrics
        """
        # Add sentiment scores to df
        df['sentiment_label'] = [r['label'] for r in sentiment_results]
        df['sentiment_score'] = [r['score'] for r in sentiment_results]
        
        # Convert sentiment labels to numeric scores
        label_to_score = {
            'SATISFIED': 90,
            'POSITIVE': 75,
            'NEUTRAL': 50,
            'NEGATIVE': 25,
            'FRUSTRATED': 10
        }
        df['sentiment_numeric'] = df['sentiment_label'].map(label_to_score)
        
        # Aggregate by technology and date
        daily_metrics = df.groupby(['technology', 'date']).agg({
            'sentiment_numeric': 'mean',
            'text': 'count',
            'sentiment_label': lambda x: x.mode()[0] if len(x) > 0 else 'NEUTRAL'
        }).reset_index()
        
        daily_metrics.columns = ['technology', 'date', 'sentiment_score', 
                                 'record_count', 'dominant_sentiment']
        
        return daily_metrics
    
    def save_to_cache(self, data: pd.DataFrame, filename: str):
        """Save processed data to cache"""
        filepath = os.path.join(self.cache_dir, filename)
        data.to_json(filepath, orient='records', date_format='iso')
        print(f"💾 Saved to cache: {filename}")
    
    def load_from_cache(self, filename: str) -> pd.DataFrame:
        """Load data from cache"""
        filepath = os.path.join(self.cache_dir, filename)
        if os.path.exists(filepath):
            return pd.read_json(filepath)
        return pd.DataFrame()


if __name__ == "__main__":
    # Test processor with mock data
    processor = DataProcessor()
    
    # Mock GitHub data
    github_data = {
        'react': [
            {
                'id': 1,
                'number': 100,
                'title': 'Bug in useEffect',
                'body': 'The hook is not working as expected',
                'state': 'open',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'comments_count': 5,
                'labels': ['bug'],
                'reactions': 3,
                'author': 'user1'
            }
        ]
    }
    
    # Process
    df = processor.process_github_issues(github_data['react'], 'react')
    print("\nProcessed Data:")
    print(df.head())