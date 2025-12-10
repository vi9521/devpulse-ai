"""
DevPulse Sentiment Analyzer
ML Model: DistilBERT fine-tuned on SST-2

This module performs sentiment analysis on developer text data
using a pre-trained transformer model with custom rules.
"""

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, List, Optional
import re

class DevSentimentAnalyzer:
    """
    Advanced NLP-based sentiment analysis for developer communications
    
    Architecture:
    1. Pre-trained DistilBERT (transfer learning)
    2. Custom rule layer for developer-specific sentiment
    3. Confidence scoring system
    """
    
    def __init__(self):
        print("Initializing DevSentimentAnalyzer...")
        
        # Load pre-trained model
        self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        self.device = 0 if torch.cuda.is_available() else -1
        
        print(f"Loading model: {self.model_name}")
        print(f"Using device: {'GPU' if self.device == 0 else 'CPU'}")
        
        # Initialize pipeline
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=self.model_name,
            device=self.device
        )
        
        # Developer-specific sentiment patterns
        self.frustration_patterns = {
            'critical': ['wtf', 'garbage', 'terrible', 'useless', 'worst'],
            'high': ['bug', 'broken', 'crash', 'error', 'failed', 'doesn\'t work'],
            'medium': ['issue', 'problem', 'confused', 'struggling', 'help']
        }
        
        self.satisfaction_patterns = {
            'high': ['love', 'amazing', 'awesome', 'excellent', 'perfect'],
            'medium': ['good', 'nice', 'works', 'helpful', 'thanks'],
            'low': ['ok', 'fine', 'decent']
        }
        
        print("✅ Sentiment Analyzer initialized successfully")
    
    def preprocess_text(self, text: str) -> str:
        """Clean and prepare text for analysis"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]*`', '', text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text[:512]  # Truncate to model max length
    
    def detect_frustration_level(self, text: str) -> tuple[str, float]:
        """
        Detect developer frustration intensity
        
        Returns:
            (level, score) where level is 'critical', 'high', 'medium', 'low'
        """
        text_lower = text.lower()
        
        # Check critical frustration
        critical_count = sum(1 for word in self.frustration_patterns['critical'] 
                           if word in text_lower)
        if critical_count >= 1:
            return ('critical', 0.95)
        
        # Check high frustration
        high_count = sum(1 for word in self.frustration_patterns['high'] 
                        if word in text_lower)
        if high_count >= 2:
            return ('high', 0.85)
        elif high_count == 1:
            return ('medium', 0.65)
        
        # Check medium frustration
        medium_count = sum(1 for word in self.frustration_patterns['medium'] 
                          if word in text_lower)
        if medium_count >= 2:
            return ('medium', 0.70)
        
        return ('low', 0.30)
    
    def detect_satisfaction_level(self, text: str) -> tuple[str, float]:
        """Detect developer satisfaction intensity"""
        text_lower = text.lower()
        
        # Check high satisfaction
        high_count = sum(1 for word in self.satisfaction_patterns['high'] 
                        if word in text_lower)
        if high_count >= 1:
            return ('high', 0.90)
        
        # Check medium satisfaction
        medium_count = sum(1 for word in self.satisfaction_patterns['medium'] 
                          if word in text_lower)
        if medium_count >= 2:
            return ('medium', 0.75)
        elif medium_count == 1:
            return ('low', 0.60)
        
        return ('none', 0.40)
    
    def analyze(self, text: str) -> Dict:
        """
        Perform comprehensive sentiment analysis
        
        Args:
            text: Developer communication text (issue, comment, etc.)
        
        Returns:
            Dict with sentiment analysis results
        """
        if not text or len(text.strip()) < 5:
            return {
                'label': 'NEUTRAL',
                'score': 0.5,
                'confidence': 'low',
                'reasoning': 'Text too short for analysis'
            }
        
        # Preprocess
        clean_text = self.preprocess_text(text)
        
        if not clean_text:
            return {
                'label': 'NEUTRAL',
                'score': 0.5,
                'confidence': 'low',
                'reasoning': 'No meaningful text after preprocessing'
            }
        
        # Base sentiment from transformer
        try:
            base_result = self.sentiment_pipeline(clean_text)[0]
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return {
                'label': 'NEUTRAL',
                'score': 0.5,
                'confidence': 'low',
                'reasoning': 'Analysis failed'
            }
        
        # Detect frustration and satisfaction
        frustration_level, frustration_score = self.detect_frustration_level(text)
        satisfaction_level, satisfaction_score = self.detect_satisfaction_level(text)
        
        # Determine final sentiment
        if frustration_level in ['critical', 'high']:
            return {
                'label': 'FRUSTRATED',
                'score': frustration_score,
                'confidence': 'high',
                'reasoning': f'{frustration_level.capitalize()} frustration detected',
                'base_sentiment': base_result['label'],
                'base_score': base_result['score'],
                'frustration_level': frustration_level,
                'satisfaction_level': satisfaction_level
            }
        
        elif satisfaction_level == 'high':
            return {
                'label': 'SATISFIED',
                'score': satisfaction_score,
                'confidence': 'high',
                'reasoning': 'High satisfaction detected',
                'base_sentiment': base_result['label'],
                'base_score': base_result['score'],
                'frustration_level': frustration_level,
                'satisfaction_level': satisfaction_level
            }
        
        else:
            # Use base model result
            label_map = {
                'POSITIVE': 'POSITIVE',
                'NEGATIVE': 'NEGATIVE'
            }
            
            return {
                'label': label_map.get(base_result['label'], 'NEUTRAL'),
                'score': base_result['score'],
                'confidence': 'medium',
                'reasoning': 'Base transformer classification',
                'base_sentiment': base_result['label'],
                'base_score': base_result['score'],
                'frustration_level': frustration_level,
                'satisfaction_level': satisfaction_level
            }
    
    def batch_analyze(self, texts: List[str], batch_size: int = 16) -> List[Dict]:
        """
        Analyze multiple texts efficiently using batching
        
        Args:
            texts: List of text strings to analyze
            batch_size: Number of texts to process at once
        
        Returns:
            List of sentiment analysis results
        """
        print(f"Analyzing {len(texts)} texts in batches of {batch_size}...")
        
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_results = [self.analyze(text) for text in batch]
            results.extend(batch_results)
            
            if (i + batch_size) % 100 == 0:
                print(f"  Processed {i + batch_size}/{len(texts)} texts")
        
        print(f"✅ Completed analysis of {len(texts)} texts")
        return results
    
    def aggregate_sentiment(self, results: List[Dict]) -> Dict:
        """
        Aggregate multiple sentiment results into summary statistics
        
        Returns:
            Dict with aggregated metrics
        """
        if not results:
            return {
                'average_score': 0.5,
                'sentiment_distribution': {},
                'frustration_rate': 0.0,
                'satisfaction_rate': 0.0
            }
        
        total = len(results)
        
        # Calculate distributions
        label_counts = {}
        total_score = 0
        frustrated_count = 0
        satisfied_count = 0
        
        for result in results:
            label = result['label']
            label_counts[label] = label_counts.get(label, 0) + 1
            total_score += result['score']
            
            if label == 'FRUSTRATED':
                frustrated_count += 1
            elif label == 'SATISFIED':
                satisfied_count += 1
        
        return {
            'average_score': total_score / total,
            'sentiment_distribution': {
                label: count / total for label, count in label_counts.items()
            },
            'frustration_rate': frustrated_count / total,
            'satisfaction_rate': satisfied_count / total,
            'total_analyzed': total,
            'dominant_sentiment': max(label_counts, key=label_counts.get)
        }


# Test the analyzer
if __name__ == "__main__":
    analyzer = DevSentimentAnalyzer()
    
    test_cases = [
        "This is completely broken! Wasted 3 hours debugging. Total garbage.",
        "Love the new update! Everything works perfectly now.",
        "How do I implement feature X? The documentation is unclear.",
        "React 18 concurrent rendering is amazing! Game changer for performance.",
        "Another bug in the build system. This is getting frustrating.",
        "The team's support has been excellent. Fixed my issue in 10 minutes."
    ]
    
    print("\n=== Sentiment Analysis Test ===\n")
    
    for text in test_cases:
        result = analyzer.analyze(text)
        print(f"Text: {text[:60]}...")
        print(f"Label: {result['label']}")
        print(f"Score: {result['score']:.2f}")
        print(f"Confidence: {result['confidence']}")
        print(f"Reasoning: {result['reasoning']}")
        print("---\n")
    
    # Test batch analysis
    print("\n=== Batch Analysis Test ===\n")
    batch_results = analyzer.batch_analyze(test_cases)
    
    # Aggregate results
    summary = analyzer.aggregate_sentiment(batch_results)
    print(f"\nAggregate Results:")
    print(f"Average Score: {summary['average_score']:.2f}")
    print(f"Frustration Rate: {summary['frustration_rate']:.1%}")
    print(f"Satisfaction Rate: {summary['satisfaction_rate']:.1%}")
    print(f"Dominant Sentiment: {summary['dominant_sentiment']}")