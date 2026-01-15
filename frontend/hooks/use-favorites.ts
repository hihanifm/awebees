"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { logger } from "@/lib/logger";

export function useFavorites() {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const fetchFavorites = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getFavorites();
      setFavorites(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch favorites");
      logger.error("Failed to fetch favorites:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFavorites();
  }, [fetchFavorites, refreshTrigger]);

  const toggleFavorite = useCallback(async (insightId: string) => {
    try {
      setError(null);
      const result = await apiClient.toggleFavorite(insightId);
      setFavorites(result.favorites);
      return result.isFavorite;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to toggle favorite";
      setError(errorMessage);
      logger.error("Failed to toggle favorite:", err);
      throw err;
    }
  }, []);

  const isFavorite = useCallback((insightId: string): boolean => {
    return favorites.includes(insightId);
  }, [favorites]);

  const refresh = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  return { 
    favorites, 
    loading, 
    error, 
    toggleFavorite, 
    isFavorite,
    refresh 
  };
}
