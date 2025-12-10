"""
DevPulse Flask API Server
Serves ML predictions and data to frontend
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.sentiment_analyzer import DevSentimentAnalyzer
from ml.trend_predictor import TrendPredictor
from api.github_collector import GitHubCollector, TECH_REPOS
from api.stackoverflow_collector import StackOverflowCollector, TECH_TAGS
from api.data_processor import DataProcessor

import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize components
print("🚀 Initializing DevPulse API...")
sentiment_analyzer = DevSentimentAnalyzer()
data_processor = DataProcessor()
github_collector = GitHubCollector()
stackoverflow_collector = StackOverflowCollector()

# Cache for data (in production, use Redis)
data_cache = {}
last_fetch_time = {}


def get_cached_or_fetch(technology: str, force_refresh: bool = False) -> Dict:
    """
    Get data from cache or fetch fresh data
    
    Args:
        technology: Technology name (e.g., 'react', 'vue')
        force_refresh: Force fetch new data
    
    Returns:
        Dict with sentiment data and metrics
    """
    cache_key = technology.lower()
    cache_duration = timedelta(hours=6)  # Refresh every 6 hours
    
    # Check cache
    if not force_refresh and cache_key in data_cache:
        last_fetch = last_fetch_time.get(cache_key)
        if last_fetch and (datetime.now() - last_fetch) < cache_duration:
            print(f"📦 Using cached data for {technology}")
            return data_cache[cache_key]
    
    print(f"🔄 Fetching fresh data for {technology}")
    
    try:
        # Fetch data from sources
        github_repo = TECH_REPOS.get(cache_key)
        stackoverflow_tag = TECH_TAGS.get(cache_key)
        
        github_issues = []
        stackoverflow_questions = []
        
        if github_repo:
            github_issues = github_collector.collect_issues(
                github_repo, 
                days=30, 
                max_issues=50
            )
        
        if stackoverflow_tag:
            stackoverflow_questions = stackoverflow_collector.collect_questions(
                stackoverflow_tag,
                days=30,
                max_questions=50
            )
        
        # Process data
        github_df = data_processor.process_github_issues(github_issues, technology)
        stackoverflow_df = data_processor.process_stackoverflow_questions(
            stackoverflow_questions, 
            technology
        )
        
        # Combine
        combined_df = pd.concat([github_df, stackoverflow_df], ignore_index=True)
        
        if combined_df.empty:
            return {
                'error': 'No data available',
                'technology': technology
            }
        
        # Analyze sentiment
        texts = combined_df['text'].tolist()
        sentiment_results = sentiment_analyzer.batch_analyze(texts)
        
        # Add sentiment to dataframe
        combined_df['sentiment_label'] = [r['label'] for r in sentiment_results]
        combined_df['sentiment_score'] = [r['score'] * 100 for r in sentiment_results]
        
        # Calculate metrics
        sentiment_summary = sentiment_analyzer.aggregate_sentiment(sentiment_results)
        
        # Prepare time-series data for predictions
        combined_df['date'] = pd.to_datetime(combined_df['created_at']).dt.date
        daily_sentiment = combined_df.groupby('date')['sentiment_score'].mean().reset_index()
        daily_sentiment.columns = ['date', 'sentiment_score']
        
        historical_data = [
            {'date': row['date'], 'sentiment_score': row['sentiment_score']}
            for _, row in daily_sentiment.iterrows()
        ]
        
        # Train predictor and forecast
        predictor = TrendPredictor()
        predictions = {'error': 'Insufficient data'}
        
        if len(historical_data) >= 10:
            success = predictor.train(historical_data, technology)
            if success:
                predictions = predictor.predict(days_ahead=7)
        
        # Detect anomalies
        anomalies = predictor.detect_anomalies(historical_data) if len(historical_data) >= 10 else []
        
        # Extract top issues
        frustrated_texts = combined_df[
            combined_df['sentiment_label'] == 'FRUSTRATED'
        ]['text'].head(10).tolist()
        
        # Build result
        result = {
            'technology': technology,
            'last_updated': datetime.now().isoformat(),
            'data_points': len(combined_df),
            'date_range': {
                'start': combined_df['date'].min().isoformat(),
                'end': combined_df['date'].max().isoformat()
            },
            'current_sentiment': {
                'score': float(sentiment_summary['average_score'] * 100),
                'label': sentiment_summary['dominant_sentiment'],
                'distribution': {
                    k: float(v) for k, v in sentiment_summary['sentiment_distribution'].items()
                }
            },
            'predictions': predictions,
            'historical_data': historical_data,
            'anomalies': anomalies,
            'top_frustrations': frustrated_texts[:5],
            'sources': {
                'github': len(github_issues),
                'stackoverflow': len(stackoverflow_questions)
            }
        }
        
        # Cache result
        data_cache[cache_key] = result
        last_fetch_time[cache_key] = datetime.now()
        
        return result
        
    except Exception as e:
        print(f"❌ Error processing {technology}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'technology': technology
        }


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'sentiment_analyzer': 'ready',
            'trend_predictor': 'ready',
            'data_collectors': 'ready'
        }
    })


@app.route('/api/technologies', methods=['GET'])
def get_technologies():
    """Get list of supported technologies"""
    return jsonify({
        'technologies': list(TECH_REPOS.keys()),
        'count': len(TECH_REPOS)
    })


@app.route('/api/sentiment/<technology>', methods=['GET'])
def get_sentiment(technology):
    """
    Get sentiment data for a technology
    
    Query params:
        - refresh: Force refresh data (default: false)
    """
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    result = get_cached_or_fetch(technology, force_refresh)
    
    if 'error' in result:
        return jsonify(result), 404 if result.get('technology') else 500
    
    return jsonify(result)


@app.route('/api/compare', methods=['POST'])
def compare_technologies():
    """
    Compare sentiment across multiple technologies
    
    Body: { "technologies": ["react", "vue", "angular"] }
    """
    data = request.json
    technologies = data.get('technologies', [])
    
    if not technologies:
        return jsonify({'error': 'No technologies provided'}), 400
    
    results = {}
    for tech in technologies:
        results[tech] = get_cached_or_fetch(tech)
    
    # Build comparison
    comparison = {
        'technologies': technologies,
        'comparison': {
            tech: {
                'score': result.get('current_sentiment', {}).get('score', 0),
                'label': result.get('current_sentiment', {}).get('label', 'UNKNOWN'),
                'data_points': result.get('data_points', 0)
            }
            for tech, result in results.items()
        },
        'ranking': sorted(
            technologies,
            key=lambda t: results[t].get('current_sentiment', {}).get('score', 0),
            reverse=True
        )
    }
    
    return jsonify(comparison)


@app.route('/api/insights/<technology>', methods=['GET'])
def get_insights(technology):
    """Get AI-generated insights for a technology"""
    data = get_cached_or_fetch(technology)
    
    if 'error' in data:
        return jsonify(data), 404
    
    # Generate insights
    current_score = data['current_sentiment']['score']
    predictions = data.get('predictions', {})
    
    insights = []
    
    # Score-based insights
    if current_score >= 80:
        insights.append({
            'type': 'positive',
            'title': f'{technology.capitalize()} developers are highly satisfied',
            'description': f'Sentiment score of {current_score:.1f}/100 indicates strong positive feedback',
            'action': f'Great time to adopt {technology} or hire {technology} developers'
        })
    elif current_score <= 40:
        insights.append({
            'type': 'warning',
            'title': f'{technology.capitalize()} developers showing frustration',
            'description': f'Low sentiment score of {current_score:.1f}/100 detected',
            'action': 'Monitor for major issues or consider alternatives'
        })
    
    # Trend-based insights
    if 'trend_direction' in predictions:
        if predictions['trend_direction'] == 'down':
            insights.append({
                'type': 'alert',
                'title': 'Declining sentiment trend detected',
                'description': f'Predicted {predictions.get("trend_strength", 0):.1f}% decrease in next 7 days',
                'action': 'Investigate recent changes or updates'
            })
        elif predictions['trend_direction'] == 'up':
            insights.append({
                'type': 'positive',
                'title': 'Improving sentiment trend',
                'description': f'Predicted {predictions.get("trend_strength", 0):.1f}% increase',
                'action': 'Good momentum for adoption or investment'
            })
    
    # Anomaly-based insights
    if data.get('anomalies'):
        recent_anomalies = [a for a in data['anomalies'] if a['type'] == 'drop']
        if recent_anomalies:
            insights.append({
                'type': 'warning',
                'title': 'Recent sentiment spike detected',
                'description': f'{len(recent_anomalies)} unusual sentiment changes in past 30 days',
                'action': 'Review recent issues or community discussions'
            })
    
    return jsonify({
        'technology': technology,
        'insights': insights,
        'generated_at': datetime.now().isoformat()
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """
    Analyze sentiment of custom text
    
    Body: { "text": "Your text here" }
    """
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = sentiment_analyzer.analyze(text)
    
    return jsonify({
        'text': text[:100] + '...' if len(text) > 100 else text,
        'sentiment': result,
        'analyzed_at': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("✅ DevPulse API Server ready!")
    print("📡 Endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/technologies")
    print("  GET  /api/sentiment/<technology>")
    print("  POST /api/compare")
    print("  GET  /api/insights/<technology>")
    print("  POST /api/analyze")
    print("\n🚀 Starting server on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)