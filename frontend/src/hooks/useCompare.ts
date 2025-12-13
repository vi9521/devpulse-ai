import { useState } from "react";
import { postCompare } from "../utils/api";

export function useCompare() {
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  async function compare(technologies: string[]) {
    setLoading(true);
    setError(null);

    try {
      const result = await postCompare(technologies);
      setComparison(result);
    } catch (err) {
      setError("Failed to fetch comparison data");
    }

    setLoading(false);
  }

  return { comparison, loading, error, compare };
}
