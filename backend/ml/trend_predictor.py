"""
DevPulse Trend Predictor
ML Model: Facebook Prophet for time-series forecasting

Predicts future sentiment trends based on historical data
"""

from prophet import Prophet
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class TrendPredictor:
    """
    Time-series forecasting for developer sentiment trends
    
    ML Concepts:
    - Additive regression model
    - Automatic seasonality detection
    - Trend change point detection
    - Uncertainty intervals
    """
    
    def __init__(self):
        self.model = None
        self.trained_on = None
        print("✅ TrendPredictor initialized")
    
    def prepare_data(self, historical_data: List[Dict]) -> pd.DataFrame:
        """
        Convert historical sentiment data to Prophet format
        
        Prophet requires:
        - 'ds': datetime column
        - 'y': metric column (sentiment score)
        """
        if not historical_data:
            return pd.DataFrame(columns=['ds', 'y'])
        
        df = pd.DataFrame(historical_data)
        
        # Ensure datetime format
        df['ds'] = pd.to_datetime(df['date'])
        df['y'] = df['sentiment_score']
        
        # Sort by date
        df = df.sort_values('ds')
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['ds'])
        
        return df[['ds', 'y']]
    
    def train(self, historical_data: List[Dict], technology: str = None):
        """
        Train Prophet model on historical sentiment data
        
        Args:
            historical_data: List of {date, sentiment_score} dicts
            technology: Optional technology name for logging
        """
        print(f"\n🔄 Training trend predictor for {technology or 'data'}...")
        
        # Prepare data
        df = self.prepare_data(historical_data)
        
        if len(df) < 10:
            print(f"⚠️ Warning: Only {len(df)} data points. Need at least 10 for reliable predictions.")
            return False
        
        print(f"  Training on {len(df)} data points")
        print(f"  Date range: {df['ds'].min()} to {df['ds'].max()}")
        
        # Initialize Prophet model
        self.model = Prophet(
            changepoint_prior_scale=0.05,  # Flexibility of trend changes
            seasonality_prior_scale=10.0,   # Strength of seasonality
            seasonality_mode='additive',     # Additive seasonality
            daily_seasonality=False,         # Disable daily seasonality
            weekly_seasonality=True,         # Enable weekly patterns
            yearly_seasonality=False,        # Disable yearly (not enough data)
            interval_width=0.95              # 95% confidence intervals
        )
        
        # Fit model
        try:
            self.model.fit(df)
            self.trained_on = technology
            print(f"✅ Model trained successfully")
            return True
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return False
    
    def predict(self, days_ahead: int = 7) -> Dict:
        """
        Predict sentiment for the next N days
        
        Args:
            days_ahead: Number of days to forecast
        
        Returns:
            Dict with predictions and confidence intervals
        """
        if not self.model:
            return {
                'error': 'Model not trained',
                'predictions': []
            }
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=days_ahead)
        
        # Make predictions
        forecast = self.model.predict(future)
        
        # Extract predictions (only future dates)
        predictions = forecast.tail(days_ahead)
        
        # Calculate trend direction
        recent_trend = predictions['yhat'].iloc[-1] - predictions['yhat'].iloc[0]
        trend_direction = 'up' if recent_trend > 0 else 'down' if recent_trend < 0 else 'stable'
        
        # Calculate confidence
        avg_uncertainty = (predictions['yhat_upper'] - predictions['yhat_lower']).mean()
        confidence = max(0, min(100, 100 - (avg_uncertainty * 100)))
        
        return {
            'technology': self.trained_on,
            'predictions': [
                {
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'predicted_score': float(row['yhat']),
                    'lower_bound': float(row['yhat_lower']),
                    'upper_bound': float(row['yhat_upper'])
                }
                for _, row in predictions.iterrows()
            ],
            'trend_direction': trend_direction,
            'trend_strength': abs(recent_trend),
            'confidence': float(confidence),
            'forecast_days': days_ahead
        }
    
    def analyze_trend(self, historical_data: List[Dict]) -> Dict:
        """
        Analyze historical trend without prediction
        
        Returns:
            Dict with trend analysis
        """
        df = self.prepare_data(historical_data)
        
        if len(df) < 2:
            return {'error': 'Insufficient data'}
        
        # Calculate moving average
        df['ma_7'] = df['y'].rolling(window=min(7, len(df))).mean()
        
        # Calculate trend
        recent_avg = df['y'].tail(7).mean()
        older_avg = df['y'].head(max(1, len(df) - 7)).mean()
        
        trend_change = ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0
        
        # Calculate volatility
        volatility = df['y'].std()
        
        return {
            'current_score': float(df['y'].iloc[-1]),
            'average_score': float(df['y'].mean()),
            'trend_change_percent': float(trend_change),
            'volatility': float(volatility),
            'data_points': len(df),
            'date_range': {
                'start': df['ds'].min().strftime('%Y-%m-%d'),
                'end': df['ds'].max().strftime('%Y-%m-%d')
            }
        }
    
    def detect_anomalies(self, historical_data: List[Dict]) -> List[Dict]:
        """
        Detect unusual sentiment changes (anomalies)
        
        Uses statistical approach:
        - Points beyond 2 standard deviations = anomalies
        """
        df = self.prepare_data(historical_data)
        
        if len(df) < 10:
            return []
        
        # Calculate statistics
        mean = df['y'].mean()
        std = df['y'].std()
        
        # Find anomalies (> 2 std deviations)
        df['is_anomaly'] = np.abs(df['y'] - mean) > (2 * std)
        
        anomalies = df[df['is_anomaly']].copy()
        
        return [
            {
                'date': row['ds'].strftime('%Y-%m-%d'),
                'score': float(row['y']),
                'deviation': float(abs(row['y'] - mean) / std),
                'type': 'spike' if row['y'] > mean else 'drop'
            }
            for _, row in anomalies.iterrows()
        ]


# Test the predictor
if __name__ == "__main__":
    # Generate mock historical data
    from datetime import datetime, timedelta
    
    base_date = datetime.now() - timedelta(days=30)
    historical_data = []
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        # Simulated sentiment with trend and noise
        score = 70 + (i * 0.5) + np.random.normal(0, 5)
        score = max(0, min(100, score))  # Clamp to 0-100
        
        historical_data.append({
            'date': date,
            'sentiment_score': score
        })
    
    # Test predictor
    predictor = TrendPredictor()
    
    # Train
    success = predictor.train(historical_data, 'React')
    
    if success:
        # Predict
        predictions = predictor.predict(days_ahead=7)
        print("\n=== Predictions ===")
        print(f"Trend Direction: {predictions['trend_direction']}")
        print(f"Confidence: {predictions['confidence']:.1f}%")
        print("\nNext 7 days:")
        for pred in predictions['predictions']:
            print(f"  {pred['date']}: {pred['predicted_score']:.1f} "
                  f"({pred['lower_bound']:.1f} - {pred['upper_bound']:.1f})")
        
        # Analyze trend
        trend_analysis = predictor.analyze_trend(historical_data)
        print("\n=== Trend Analysis ===")
        print(f"Current Score: {trend_analysis['current_score']:.1f}")
        print(f"Average Score: {trend_analysis['average_score']:.1f}")
        print(f"Trend Change: {trend_analysis['trend_change_percent']:.1f}%")
        print(f"Volatility: {trend_analysis['volatility']:.1f}")
        
        # Detect anomalies
        anomalies = predictor.detect_anomalies(historical_data)
        if anomalies:
            print("\n=== Anomalies Detected ===")
            for anomaly in anomalies:
                print(f"  {anomaly['date']}: {anomaly['score']:.1f} "
                      f"({anomaly['type']}, {anomaly['deviation']:.1f}σ)")