"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { InsightMetadata } from "@/lib/api-types";

export function useInsights() {
  const [insights, setInsights] = useState<InsightMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const fetchInsights = useCallback(async () => {
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
  }, []);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights, refreshTrigger]);

  const refresh = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  return { insights, loading, error, refresh };
}

