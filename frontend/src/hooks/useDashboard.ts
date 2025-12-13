import { useEffect, useState, useCallback } from "react";
import { getSentiment, getInsights } from "../utils/api";

export function useDashboard(technology: string) {
  const [sentiment, setSentiment] = useState<any>(null);
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (force = false) => {
    setLoading(true);
    setError(null);

    try {
      const sentimentRes = await getSentiment(technology, force);
      const insightsRes = await getInsights(technology);

      setSentiment(sentimentRes);
      setInsights(insightsRes.insights || []);
    } catch (err) {
      console.error(err);
      setError("Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, [technology]);

  useEffect(() => {
    load(false);
  }, [load]);

  return {
    sentiment,
    insights,
    loading,
    error,
    refresh: () => load(true),
  };
}
