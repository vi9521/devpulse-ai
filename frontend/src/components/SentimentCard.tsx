import React from "react";

interface Props {
  label: string;
  value: number;
}

export default function SentimentCard({ label, value }: Props) {
  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-md flex flex-col items-center">
      <span className="text-lg text-gray-300">{label}</span>
      <h2 className="text-3xl font-bold mt-2">{value}%</h2>
    </div>
  );
}
