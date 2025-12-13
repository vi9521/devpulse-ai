interface Props {
  label: string;
  value: number;
}

export default function SentimentCard({ label, value }: Props) {
  return (
    <div className="bg-gray-800 border border-gray-700 p-6 rounded-xl text-center shadow-md">
      <p className="text-gray-400 text-sm mb-2">{label}</p>
      <p className="text-4xl font-bold text-green-400">{value}%</p>
    </div>
  );
}
