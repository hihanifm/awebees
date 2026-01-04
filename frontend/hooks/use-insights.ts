"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { InsightMetadata } from "@/lib/api-types";

export function useInsights() {
  const [insights, setInsights] = useState<InsightMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.getInsights();
        setInsights(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch insights");
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, []);

  return { insights, loading, error };
}

