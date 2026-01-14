"use client";

import { useState, useEffect } from "react";
import { Shield } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { logger } from "@/lib/logger";

export function SafeModeBanner() {
  const [safeMode, setSafeMode] = useState(false);

  useEffect(() => {
    const loadSafeMode = async () => {
      try {
        const state = await apiClient.getSafeMode();
        setSafeMode(state.enabled);
      } catch (error) {
        logger.error("Failed to load safe mode:", error);
      }
    };

    loadSafeMode();
    
    // Listen for custom events when safe mode changes
    // Note: Safe mode changes require restart to take effect, so no polling needed
    const handleSafeModeChange = () => {
      loadSafeMode();
    };
    window.addEventListener("safe-mode-changed", handleSafeModeChange);
    
    return () => {
      window.removeEventListener("safe-mode-changed", handleSafeModeChange);
    };
  }, []);

  if (!safeMode) {
    return null;
  }

  return (
    <div className="fixed top-16 left-0 right-0 z-40 w-full bg-yellow-500 dark:bg-yellow-600 text-yellow-900 dark:text-yellow-100 px-4 py-2 flex items-center gap-2">
      <Shield className="h-4 w-4" />
      <span className="text-sm font-medium">
        Safe Mode Active - External insights and samples disabled
      </span>
    </div>
  );
}
