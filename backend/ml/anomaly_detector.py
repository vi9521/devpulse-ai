"""
Anomaly Detector for DevPulse

Detects anomalous days or events in time-series sentiment/engagement data
using statistical rules and an Isolation Forest ensemble.

Outputs:
- point anomalies (single-day spikes/drops)
- contextual anomalies (windows that deviate from local behaviour)
"""

from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


class AnomalyDetector:
    def __init__(self, contamination: float = 0.01, random_state: int = 42):
        """
        Args:
            contamination: expected fraction of anomalies (IsolationForest)
            random_state: RNG seed for reproducibility
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None
        print("✅ AnomalyDetector initialized")

    def _to_dataframe(self, historical_data: List[Dict]) -> pd.DataFrame:
        """
        Convert list of dicts {'date': ..., 'sentiment_score': ...} to DataFrame
        """
        if not historical_data:
            return pd.DataFrame(columns=["ds", "y"])

        df = pd.DataFrame(historical_data)
        # Normalize column names
        if "date" in df.columns:
            df["ds"] = pd.to_datetime(df["date"])
        elif "ds" in df.columns:
            df["ds"] = pd.to_datetime(df["ds"])
        else:
            raise ValueError("historical_data must contain 'date' or 'ds' field")

        if "sentiment_score" in df.columns:
            df["y"] = pd.to_numeric(df["sentiment_score"], errors="coerce")
        elif "y" in df.columns:
            df["y"] = pd.to_numeric(df["y"], errors="coerce")
        else:
            raise ValueError("historical_data must contain 'sentiment_score' or 'y' field")

        df = df.sort_values("ds").dropna(subset=["y"])
        df = df.reset_index(drop=True)
        return df[["ds", "y"]]

    def detect_statistical_anomalies(self, historical_data: List[Dict], z_thresh: float = 2.5) -> List[Dict]:
        """
        Simple z-score based anomaly detection.

        Returns list of anomalies with date, value and z-score.
        """
        df = self._to_dataframe(historical_data)
        if df.empty:
            return []

        mean = df["y"].mean()
        std = df["y"].std(ddof=0) if df.shape[0] > 1 else 0.0
        if std == 0:
            return []

        df["z"] = (df["y"] - mean) / std
        anomalies = df[np.abs(df["z"]) >= z_thresh]

        return [
            {
                "date": row["ds"].strftime("%Y-%m-%d"),
                "value": float(row["y"]),
                "z_score": float(row["z"]),
                "type": "spike" if row["z"] > 0 else "drop"
            }
            for _, row in anomalies.iterrows()
        ]

    def fit_isolation_forest(self, historical_data: List[Dict]):
        """
        Fit an Isolation Forest on the sentiment values.
        """
        df = self._to_dataframe(historical_data)
        if df.empty or len(df) < 5:
            self.model = None
            return False

        X = df["y"].values.reshape(-1, 1)
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
            behaviour="new" if hasattr(IsolationForest(), "behaviour") else None
        )
        # Some sklearn versions don't accept None for behaviour; ignore if fails
        try:
            self.model.fit(X)
        except TypeError:
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_estimators=100
            )
            self.model.fit(X)

        return True

    def detect_iforest_anomalies(self, historical_data: List[Dict]) -> List[Dict]:
        """
        Use a trained IsolationForest to find anomalies.
        """
        df = self._to_dataframe(historical_data)
        if df.empty:
            return []

        # Fit model if needed
        if self.model is None:
            ok = self.fit_isolation_forest(historical_data)
            if not ok:
                return []

        X = df["y"].values.reshape(-1, 1)
        preds = self.model.predict(X)  # -1 for anomaly, 1 for normal

        df["anomaly"] = preds == -1
        anomalies = df[df["anomaly"]]

        # Use anomaly score if available
        try:
            scores = self.model.decision_function(X)
        except Exception:
            scores = np.zeros(len(X))

        results = []
        for idx, row in anomalies.iterrows():
            results.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "value": float(row["y"]),
                "anomaly_score": float(scores[idx]) if len(scores) > idx else None,
                "type": "spike" if row["y"] > df["y"].mean() else "drop"
            })
        return results

    def detect_window_anomalies(self, historical_data: List[Dict], window: int = 7, threshold: float = 0.25) -> List[Dict]:
        """
        Detect contextual anomalies where a window's mean deviates from a rolling baseline by 'threshold' proportion.

        threshold: fraction (e.g., 0.25 = 25% change)
        """
        df = self._to_dataframe(historical_data)
        if df.empty or len(df) < window * 2:
            return []

        df["rolling_mean"] = df["y"].rolling(window=window, min_periods=1).mean()
        df["baseline"] = df["y"].rolling(window=window * 2, min_periods=1).mean().shift(window)
        df = df.dropna(subset=["baseline"])

        anomalies = []
        for _, row in df.iterrows():
            baseline = row["baseline"]
            if baseline == 0:
                continue
            change = (row["rolling_mean"] - baseline) / baseline
            if abs(change) >= threshold:
                anomalies.append({
                    "date": row["ds"].strftime("%Y-%m-%d"),
                    "rolling_mean": float(row["rolling_mean"]),
                    "baseline": float(baseline),
                    "relative_change": float(change),
                    "type": "spike" if change > 0 else "drop"
                })
        return anomalies


# Quick test harness
if __name__ == "__main__":
    # create synthetic series with anomalies
    from datetime import timedelta
    base = datetime.now().date() - timedelta(days=30)
    data = []
    for i in range(31):
        date = base + timedelta(days=i)
        value = 50 + np.sin(i / 3.0) * 5 + np.random.normal(0, 1)
        # insert a spike
        if i == 10:
            value += 30
        if i == 22:
            value -= 25
        data.append({"date": date, "sentiment_score": float(value)})

    detector = AnomalyDetector(contamination=0.05)
    stat = detector.detect_statistical_anomalies(data, z_thresh=2.5)
    iforest_ok = detector.fit_isolation_forest(data)
    iforest = detector.detect_iforest_anomalies(data)
    window = detector.detect_window_anomalies(data, window=7, threshold=0.2)

    print("Statistical anomalies:", stat)
    print("IForest anomalies:", iforest)
    print("Window anomalies:", window)
