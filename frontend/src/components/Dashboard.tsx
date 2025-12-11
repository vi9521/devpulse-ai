import SentimentCard from "./SentimentCard";
import TrendChart from "./TrendChart";
import InsightPanel from "./InsightPanel";
import PredictionEngine from "./PredictionEngine";
import ComparisonTool from "./ComparisonTool";

export default function Dashboard() {
  const sampleTrend = [
    { date: "Mon", score: 60 },
    { date: "Tue", score: 64 },
    { date: "Wed", score: 68 },
    { date: "Thu", score: 72 },
    { date: "Fri", score: 71 },
  ];

  const insights = [
    "React shows rising positive sentiment this week.",
    "Python discussions increased 17% in engagement.",
    "StackOverflow activity shows fewer bug reports.",
  ];

  const prediction = {
    direction: "up",
    confidence: 87,
  };

  const comparisonData = [
    { tech: "React", score: 72 },
    { tech: "Vue", score: 65 },
    { tech: "Angular", score: 59 },
    { tech: "Django", score: 76 },
    { tech: "Flask", score: 68 },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <SentimentCard label="Positive Sentiment" value={72} />
      <SentimentCard label="Negative Sentiment" value={18} />
      <SentimentCard label="Frustration Level" value={10} />

      <div className="md:col-span-2">
        <TrendChart data={sampleTrend} />
      </div>

      <InsightPanel insights={insights} />

      <PredictionEngine prediction={prediction} />

      <div className="md:col-span-3">
        <ComparisonTool data={comparisonData} />
      </div>
    </div>
  );
}
