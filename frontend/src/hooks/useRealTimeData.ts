// frontend/src/hooks/useRealTimeData.ts
import { useEffect, useState, useCallback } from "react";
import { getTechnologies, getSentiment, getInsights } from "../utils/api";

export function useRealTimeData(initialTech = "react") {
  const [technologies, setTechnologies] = useState<string[]>([]);
  const [selectedTech, setSelectedTech] = useState<string>(initialTech);

  const [sentimentData, setSentimentData] = useState<any>(null);
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTechnologies = useCallback(async () => {
    try {
      const data = await getTechnologies();
      setTechnologies(data.technologies || []);
    } catch (e: any) {
      console.error("getTechnologies error", e);
      setError(e?.message || "Failed to load technologies");
    }
  }, []);

  const fetchAllFor = useCallback(
    async (tech: string, forceRefresh = false) => {
      setLoading(true);
      setError(null);
      try {
        const sentiment = await getSentiment(tech, forceRefresh);
        setSentimentData(sentiment);
      } catch (e: any) {
        console.error("getSentiment error", e);
        setError(e?.message || "Failed to fetch sentiment");
        setSentimentData(null);
      }

      try {
        const ins = await getInsights(tech);
        setInsights(ins.insights || []);
      } catch (e: any) {
        console.error("getInsights error", e);
        // don't overwrite sentiment error
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // initial load
  useEffect(() => {
    fetchTechnologies();
    fetchAllFor(selectedTech, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // change technology
  useEffect(() => {
    fetchAllFor(selectedTech, false);
  }, [selectedTech, fetchAllFor]);

  return {
    technologies,
    selectedTech,
    setSelectedTech,
    sentimentData,
    insights,
    loading,
    error,
    refresh: (force = true) => fetchAllFor(selectedTech, force),
  };
}
