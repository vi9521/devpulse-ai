import {
  LineChart,
  Line,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: { date: string; score: number }[];
}

export default function TrendChart({ data }: Props) {
  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-md">
      <h2 className="text-xl mb-4 font-semibold">Sentiment Trend</h2>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid stroke="#444" />
          <XAxis dataKey="date" stroke="#ccc" />
          <YAxis stroke="#ccc" />
          <Tooltip />
          <Line type="monotone" dataKey="score" stroke="#4ADE80" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
