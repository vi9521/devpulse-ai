import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: { tech: string; score: number }[];
}

export default function ComparisonTool({ data }: Props) {
  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-md">
      <h2 className="text-xl mb-4 font-semibold">Tech Comparison</h2>

      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="tech" stroke="#fff" />
          <Radar
            name="Sentiment"
            dataKey="score"
            stroke="#4ADE80"
            fill="#4ADE80"
            fillOpacity={0.5}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
