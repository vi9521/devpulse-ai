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

from datetime import datetime, timedelta
import pandas as pd
from typing import Dict

app = Flask(__name__)
CORS(app)

# ---------------- ERROR HANDLERS ---------------- #

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/api/health",
            "/api/technologies",
            "/api/sentiment/<technology>",
            "/api/compare",
            "/api/insights/<technology>",
            "/api/analyze",
            "/api/stats"
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong on the server"
    }), 500


# ---------------- INITIALIZATION ---------------- #

print("🚀 Initializing DevPulse API...")

sentiment_analyzer = DevSentimentAnalyzer()
data_processor = DataProcessor()
github_collector = GitHubCollector()
stackoverflow_collector = StackOverflowCollector()

data_cache: Dict[str, dict] = {}
last_fetch_time: Dict[str, datetime] = {}

CACHE_DURATION = timedelta(hours=6)

# ---------------- CORE LOGIC ---------------- #

def get_cached_or_fetch(technology: str, force_refresh: bool = False) -> Dict:
    key = technology.lower()

    if not force_refresh and key in data_cache:
        if datetime.now() - last_fetch_time[key] < CACHE_DURATION:
            print(f"📦 Using cached data for {technology}")
            return data_cache[key]

    print(f"🔄 Fetching fresh data for {technology}")

    github_repo = TECH_REPOS.get(key)
    stack_tag = TECH_TAGS.get(key)

    github_issues = github_collector.collect_issues(github_repo, 30, 50) if github_repo else []
    stack_questions = stackoverflow_collector.collect_questions(stack_tag, 30, 50) if stack_tag else []

    github_df = data_processor.process_github_issues(github_issues, technology)
    stack_df = data_processor.process_stackoverflow_questions(stack_questions, technology)

    combined = pd.concat([github_df, stack_df], ignore_index=True)

    if combined.empty:
        return {"error": "No data available", "technology": technology}

    texts = combined["text"].tolist()
    results = sentiment_analyzer.batch_analyze(texts)

    combined["sentiment_label"] = [r["label"] for r in results]
    combined["sentiment_score"] = [r["score"] * 100 for r in results]

    summary = sentiment_analyzer.aggregate_sentiment(results)

    combined["date"] = pd.to_datetime(combined["created_at"]).dt.date
    daily = combined.groupby("date")["sentiment_score"].mean().reset_index()

    history = [{"date": r["date"].isoformat(), "sentiment_score": r["sentiment_score"]} for _, r in daily.iterrows()]

    predictor = TrendPredictor()
    predictions = predictor.predict(7) if predictor.train(history, technology) else {}

    result = {
        "technology": technology,
        "last_updated": datetime.now().isoformat(),
        "data_points": len(combined),
        "current_sentiment": {
            "score": summary["average_score"] * 100,
            "label": summary["dominant_sentiment"],
            "distribution": summary["sentiment_distribution"]
        },
        "historical_data": history,
        "predictions": predictions,
        "sources": {
            "github": len(github_issues),
            "stackoverflow": len(stack_questions)
        }
    }

    data_cache[key] = result
    last_fetch_time[key] = datetime.now()

    return result


# ---------------- ROUTES ---------------- #

@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "time": datetime.now().isoformat()})


@app.route("/api/technologies")
def technologies():
    return jsonify({"technologies": list(TECH_REPOS.keys())})


@app.route("/api/sentiment/<technology>")
def sentiment(technology):
    refresh = request.args.get("refresh") == "true"
    return jsonify(get_cached_or_fetch(technology, refresh))


@app.route("/api/compare", methods=["POST"])
def compare():
    techs = request.json.get("technologies", [])
    return jsonify({
        "comparison": {
            t: get_cached_or_fetch(t)["current_sentiment"]["score"] for t in techs
        }
    })


@app.route("/api/insights/<technology>")
def insights(technology):
    data = get_cached_or_fetch(technology)
    score = data["current_sentiment"]["score"]

    return jsonify({
        "technology": technology,
        "insights": [{
            "description": f"Sentiment score is {score:.1f}/100"
        }]
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "")
    return jsonify(sentiment_analyzer.analyze(text))


@app.route("/api/stats")
def stats():
    return jsonify({
        "cached": list(data_cache.keys()),
        "cache_size": len(data_cache)
    })


# ---------------- SERVER START ---------------- #

if __name__ == "__main__":
    print("✅ DevPulse API Server ready")
    print("🚀 Running on http://localhost:5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,        # ❌ DO NOT ENABLE
        use_reloader=False # ❌ VERY IMPORTANT
    )
