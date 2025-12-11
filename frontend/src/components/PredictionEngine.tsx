interface Props {
  prediction: {
    direction: string;
    confidence: number;
  };
}

export default function PredictionEngine({ prediction }: Props) {
  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-md">
      <h2 className="text-xl mb-4 font-semibold">ML Prediction</h2>

      <p className="text-gray-300">Trend Direction:</p>
      <h3 className="text-2xl font-bold text-green-400 capitalize">
        {prediction.direction}
      </h3>

      <p className="text-gray-300 mt-4">Confidence:</p>
      <h3 className="text-2xl font-bold text-blue-400">
        {prediction.confidence}%
      </h3>
    </div>
  );
}
