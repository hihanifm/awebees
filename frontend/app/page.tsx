"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { InsightList } from "@/components/insight-list/InsightList";
import { ResultsPanel } from "@/components/results-panel/ResultsPanel";
import { ProgressWidget } from "@/components/progress/ProgressWidget";
import { ErrorBanner } from "@/components/ErrorBanner";
import { StatusBar } from "@/components/StatusBar";
import { CustomParamsInput } from "@/components/custom-params/CustomParamsInput";
import { apiClient } from "@/lib/api-client";
import { AnalysisResponse, ProgressEvent, ErrorEvent } from "@/lib/api-types";
import { useTranslation } from "@/lib/i18n";
import { logger } from "@/lib/logger";
import { savePath, getMostRecentPath, getCachedPaths } from "@/lib/path-storage";

/**
 * Strip surrounding quotes from a string if they match at both ends.
 * Handles both single quotes (') and double quotes (").
 * Only strips if quotes are matched (same type at start and end).
 */
function stripQuotes(path: string): string {
  if (!path || path.length < 2) {
    return path;
  }

  const first = path[0];
  const last = path[path.length - 1];

  // Only strip if both ends have the same quote type
  if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
    return path.slice(1, -1);
  }

  return path;
}

export default function Home() {
  const { t } = useTranslation();
  const [filePaths, setFilePaths] = useState<string>("");
  const [selectedInsightIds, setSelectedInsightIds] = useState<string[]>([]);
  const [analysisResponse, setAnalysisResponse] = useState<AnalysisResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [backendErrors, setBackendErrors] = useState<ErrorEvent[]>([]);
  const [availableSamples, setAvailableSamples] = useState<any[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string | null>(null);
  const [cachedPaths, setCachedPaths] = useState<string[]>([]);
  const [customParams, setCustomParams] = useState<Record<string, any> | undefined>(undefined);
  const [selectedCachedPath, setSelectedCachedPath] = useState<string>("");

  // Stream backend errors on mount
  useEffect(() => {
    const streamErrors = async () => {
      try {
        await apiClient.streamErrors((error: ErrorEvent) => {
          setBackendErrors((prev) => [...prev, error]);
        });
      } catch (err) {
        logger.error("Failed to stream errors:", err);
      }
    };

    streamErrors();
  }, []);

  const handleDismissError = (index: number) => {
    setBackendErrors((prev) => prev.filter((_, i) => i !== index));
  };

  // Load last used paths from localStorage on mount
  useEffect(() => {
    const lastPath = getMostRecentPath();
    if (lastPath) {
      setFilePaths(lastPath);
    }
    // Load cached paths for dropdown
    setCachedPaths(getCachedPaths());
  }, []);

  // Load available samples on mount and auto-select first one
  useEffect(() => {
    const loadSamples = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/files/samples`);
        if (response.ok) {
          const data = await response.json();
          if (data.samples && data.samples.length > 0) {
            setAvailableSamples(data.samples);
            // Auto-select first available sample
            const firstSample = data.samples.find((s: any) => s.exists) || data.samples[0];
            if (firstSample) {
              setSelectedSampleId(firstSample.id);
              // Auto-load the first sample
              if (firstSample.exists) {
                setFilePaths(firstSample.path);
                savePath(firstSample.path);
                setCachedPaths(getCachedPaths());
              }
            }
          }
        }
      } catch (err) {
        logger.error("Failed to load samples:", err);
      }
    };
    
    loadSamples();
  }, []);

  // Auto-load sample when selection changes
  useEffect(() => {
    if (selectedSampleId && availableSamples.length > 0) {
      const selectedSample = availableSamples.find(s => s.id === selectedSampleId);
      if (selectedSample && selectedSample.exists) {
        setFilePaths(selectedSample.path);
        savePath(selectedSample.path);
        setCachedPaths(getCachedPaths());
      }
    }
  }, [selectedSampleId, availableSamples]);

  const handleCancel = async () => {
    if (currentTaskId) {
      try {
        await apiClient.cancelAnalysis(currentTaskId);
        setAnalyzing(false);
      } catch (err) {
        logger.error("Error cancelling analysis:", err);
      }
    }
  };


  const handleAnalyze = async () => {
    if (selectedInsightIds.length === 0) {
      setError("Please select at least one insight");
      return;
    }

    const paths = filePaths
      .split("\n")
      .map((p) => p.trim())
      .map((p) => stripQuotes(p))
      .filter((p) => p.length > 0);

    if (paths.length === 0) {
      setError("Please enter at least one file or folder path");
      return;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysisResponse(null);
    setProgressEvents([]);
    setCurrentTaskId(null);

    try {
      // Save paths to cache
      savePath(filePaths);
      setCachedPaths(getCachedPaths());

      // Add initial progress event to show widget immediately
      setProgressEvents([{
        type: "file_selection",
        message: "Selecting files...",
        task_id: "pending",
        timestamp: new Date().toISOString(),
      }]);

      // Validate paths (selectFiles validates and returns paths as-is, no expansion)
      const selectResponse = await apiClient.selectFiles(paths);

      if (selectResponse.files.length === 0) {
        // Check if original input might have spaces (wrong delimiter)
        const hasSpacesInInput = filePaths.trim().includes(" ") && !filePaths.trim().includes("\n");
        let errorMessage = hasSpacesInInput
          ? "No valid paths found. Make sure each path is on a separate line (use Enter/Return, not spaces)."
          : `No valid paths found. Please check that the paths exist and are accessible. You provided ${paths.length} path(s).`;
        
        // Add info about invalid paths if available
        if (selectResponse.invalid_paths && selectResponse.invalid_paths.length > 0) {
          errorMessage += ` Invalid path(s): ${selectResponse.invalid_paths.join(", ")}`;
        }
        
        setError(errorMessage);
        setProgressEvents([]); // Clear progress events to avoid stuck state
        setAnalyzing(false);
        return;
      }
      
      // Warn about invalid paths but continue with valid ones
      // Store invalid paths warning to show even after analysis completes
      let invalidPathsWarning: string | null = null;
      if (selectResponse.invalid_paths && selectResponse.invalid_paths.length > 0) {
        invalidPathsWarning = `Some paths were invalid and skipped: ${selectResponse.invalid_paths.join(", ")}. Processing ${selectResponse.files.length} valid path(s).`;
        logger.warn(invalidPathsWarning);
        setError(invalidPathsWarning); // Show warning in UI
      }

      // Extract task ID from first progress event
      let taskIdExtracted = false;

      // Run analysis with progress tracking (API will call analyze() once per path)
      const response = await apiClient.analyzeWithProgress(
        selectedInsightIds,
        selectResponse.files,
        (event: ProgressEvent) => {
          setProgressEvents((prev) => [...prev, event]);
          if (!taskIdExtracted && event.task_id) {
            setCurrentTaskId(event.task_id);
            taskIdExtracted = true;
          }
          // Note: path_result events are collected by the API and included in the final result event
          // We could handle them here for incremental UI updates, but for now we wait for the final result
        }
      );

      // Set final response (contains all path results)
      setAnalysisResponse(response);
      // Keep invalid paths warning visible after analysis completes
      if (invalidPathsWarning) {
        setError(invalidPathsWarning);
      }
    } catch (err) {
      if (err instanceof Error && err.message === "Analysis cancelled") {
        setError(t("errors.analysisCancelled"));
      } else {
        setError(err instanceof Error ? err.message : t("errors.analysisFailed"));
      }
    } finally {
      setAnalyzing(false);
      setCurrentTaskId(null);
    }
  };

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5 font-sans">
      <main className="flex min-h-screen w-full max-w-[90%] flex-col gap-8 pb-8 px-4 mx-auto bg-background/80 backdrop-blur-sm border-x border-border pt-8">
        {/* Backend Errors Banner */}
        {backendErrors.length > 0 && (
          <section>
            <ErrorBanner errors={backendErrors} onDismiss={handleDismissError} />
          </section>
        )}

        <div className="space-y-8">
              {/* File Selection */}
              <section>
                <h2 className="text-lg font-semibold mb-4">{t("app.enterFilePaths")}</h2>
            <div className="space-y-2">
              {cachedPaths.length > 0 && (
                <div className="flex items-center gap-2">
                  <label className="text-xs text-muted-foreground whitespace-nowrap">
                    Recent paths:
                  </label>
                  <Select
                    value={selectedCachedPath || undefined}
                    onValueChange={(value) => {
                      setFilePaths(value);
                      // Reset after a short delay to allow Select to close
                      setTimeout(() => setSelectedCachedPath(""), 100);
                    }}
                    disabled={analyzing}
                  >
                    <SelectTrigger className="w-full text-left">
                      <SelectValue placeholder="Select a recent path..." />
                    </SelectTrigger>
                    <SelectContent>
                      {cachedPaths.map((path) => (
                        <SelectItem key={path} value={path}>
                          <span className="font-mono text-sm truncate block" title={path}>
                            {path}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <textarea
                value={filePaths}
                onChange={(e) => setFilePaths(e.target.value)}
                placeholder={t("app.filePathsPlaceholder")}
                className="w-full h-[3.5rem] rounded-md border border-input bg-muted px-4 py-2 font-mono text-sm resize-y"
                rows={2}
                disabled={analyzing}
              />
              {availableSamples.length > 0 && (
                <div className="flex items-center gap-2">
                  <label className="text-xs text-muted-foreground whitespace-nowrap">
                    {t("app.selectSample")}:
                  </label>
                  <Select
                    value={selectedSampleId || ""}
                    onValueChange={setSelectedSampleId}
                    disabled={analyzing}
                  >
                    <SelectTrigger className="w-full text-left">
                      <SelectValue placeholder={t("app.selectSamplePlaceholder")} />
                    </SelectTrigger>
                    <SelectContent>
                      {availableSamples.map((sample) => (
                        <SelectItem key={sample.id} value={sample.id}>
                          <div className="flex flex-col items-start text-left">
                            <span className="font-medium">{sample.name}</span>
                            {sample.description && (
                              <span className="text-xs text-muted-foreground text-left">
                                {sample.description}
                              </span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                {t("app.filePathsHint")}
              </p>
            </div>
          </section>

          {/* Insight Selection */}
          <section>
            <h2 className="text-lg font-semibold mb-4">{t("app.selectInsights")}</h2>
            <InsightList
              selectedInsightIds={selectedInsightIds}
              onSelectionChange={setSelectedInsightIds}
            />
            <CustomParamsInput value={customParams} onChange={setCustomParams} />
          </section>

          {/* Progress Widget */}
          {(analyzing || progressEvents.length > 0) && (
            <section>
              <ProgressWidget
                events={progressEvents}
                currentTaskId={currentTaskId}
                onCancel={handleCancel}
              />
            </section>
          )}

          {/* Analyze Button */}
          <section>
            <Button
              onClick={handleAnalyze}
              disabled={analyzing || selectedInsightIds.length === 0 || !filePaths.trim()}
              className="w-full font-bold"
            >
              {analyzing ? t("app.analyzing") : t("app.analyzeFiles")}
            </Button>
            {error && (
              <div className="mt-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
                <p className="text-sm text-red-600 dark:text-red-400">{t("common.error")}: {error}</p>
              </div>
            )}
          </section>

          {/* Results */}
          {analysisResponse && (
            <section>
              <ResultsPanel 
                analysisResponse={analysisResponse} 
                loading={analyzing}
              />
            </section>
          )}
        </div>
      </main>

      {/* Status Bar */}
      <StatusBar />
    </div>
  );
}
