interface Props {
  insights: string[];
}

export default function InsightPanel({ insights }: Props) {
  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-md">
      <h2 className="text-xl mb-4 font-semibold">AI Insights</h2>

      <ul className="space-y-2">
        {insights.map((item, i) => (
          <li key={i} className="p-2 bg-gray-700 rounded">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
