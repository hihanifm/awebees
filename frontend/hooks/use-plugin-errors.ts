"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { ErrorEvent } from "@/lib/api-types";
import { logger } from "@/lib/logger";

/**
 * Hook to listen for plugin load errors and manage error dialogs.
 * Shows critical errors (error, critical severity) as dialogs immediately.
 */
export function usePluginErrors() {
  const [currentError, setCurrentError] = useState<ErrorEvent | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [seenErrorIds, setSeenErrorIds] = useState<Set<string>>(new Set());

  // Generate a unique ID for an error to avoid showing duplicates
  const getErrorId = useCallback((error: ErrorEvent): string => {
    return `${error.type}-${error.file || 'unknown'}-${error.insight_id || 'unknown'}-${error.message}`;
  }, []);

  // Show error in dialog if it's critical
  const handleError = useCallback((error: ErrorEvent) => {
    const errorId = getErrorId(error);
    
    // Skip if we've already shown this error
    if (seenErrorIds.has(errorId)) {
      return;
    }

    // Only show critical errors (error or critical severity) as dialogs
    const isCritical = error.severity === "error" || error.severity === "critical";
    
    if (isCritical) {
      setCurrentError(error);
      setIsDialogOpen(true);
      setSeenErrorIds(prev => new Set([...prev, errorId]));
      logger.error("Plugin load error detected:", error);
    } else {
      // Log warnings but don't show as dialog
      logger.warn("Plugin load warning:", error);
    }
  }, [getErrorId, seenErrorIds]);

  // Stream errors from backend
  useEffect(() => {
    let isMounted = true;

    const streamErrors = async () => {
      try {
        await apiClient.streamErrors((error: ErrorEvent) => {
          if (isMounted) {
            handleError(error);
          }
        });
      } catch (err) {
        logger.error("Failed to stream plugin errors:", err);
      }
    };

    streamErrors();

    return () => {
      isMounted = false;
    };
  }, [handleError]);

  const closeDialog = useCallback(() => {
    setIsDialogOpen(false);
    // Keep currentError so it can be reopened if needed
  }, []);

  return {
    currentError,
    isDialogOpen,
    closeDialog,
  };
}
