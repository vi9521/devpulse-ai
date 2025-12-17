import SentimentCard from "./SentimentCard";
import TrendChart from "./TrendChart";
import InsightPanel from "./InsightPanel";
import PredictionEngine from "./PredictionEngine";
import { useDashboard } from "../hooks/useDashboard";

export default function Dashboard() {
  const { sentiment, insights, loading, error, refresh } =
    useDashboard("react");

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-300">
        <p className="text-lg font-medium">
          ⏳ Fetching live developer data
        </p>
        <p className="text-sm mt-2">
          First load may take a minute (real ML + APIs)
        </p>
      </div>
    );
  }

  if (error || !sentiment) {
    return (
      <p className="text-center text-red-400">
        {error ?? "Failed to load dashboard data."}
      </p>
    );
  }

  const dist = sentiment.current_sentiment.distribution;
  const pct = (v: number) => Math.round(v * 100);

  return (
    <>
      {/* 🔄 Refresh */}
      <div className="flex justify-end mb-4">
        <button
          onClick={refresh}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium"
        >
          🔄 Refresh Live Data
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SentimentCard label="Positive Sentiment" value={pct(dist.POSITIVE ?? 0)} />
        <SentimentCard label="Negative Sentiment" value={pct(dist.NEGATIVE ?? 0)} />
        <SentimentCard
          label="Frustration Level"
          value={pct(dist.FRUSTRATED ?? 0)}
        />

        <div className="md:col-span-2">
       <TrendChart
  data={sentiment.historical_data}

         />

        </div>

        <InsightPanel insights={insights.map((i: any) => i.description)} />

        <PredictionEngine
          prediction={{
            direction: sentiment.predictions.trend_direction || "none",
            confidence: Math.round(
              sentiment.predictions.trend_strength || 0
            ),
          }}
        />
      </div>
    </>
  );
}
