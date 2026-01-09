"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { InsightList } from "@/components/insight-list/InsightList";
import { ResultsPanel } from "@/components/results-panel/ResultsPanel";
import { ProgressWidget } from "@/components/progress/ProgressWidget";
import { ErrorBanner } from "@/components/ErrorBanner";
import { SettingsDialog } from "@/components/settings/SettingsDialog";
import { StatusBar } from "@/components/StatusBar";
import { apiClient } from "@/lib/api-client";
import { AnalysisResponse, ProgressEvent, ErrorEvent } from "@/lib/api-types";
import { useTranslation } from "@/lib/i18n";
import { logger } from "@/lib/logger";

const LAST_PATH_KEY = "lens_last_file_paths";

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
  const [loadingSample, setLoadingSample] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [availableSamples, setAvailableSamples] = useState<any[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string | null>(null);

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
    const lastPaths = localStorage.getItem(LAST_PATH_KEY);
    if (lastPaths) {
      setFilePaths(lastPaths);
    }
  }, []);

  // Load available samples on mount
  useEffect(() => {
    const loadSamples = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/files/samples`);
        if (response.ok) {
          const data = await response.json();
          if (data.samples && data.samples.length > 0) {
            setAvailableSamples(data.samples);
            // Auto-select first sample if only one available
            if (data.samples.length === 1) {
              setSelectedSampleId(data.samples[0].id);
            }
          }
        }
      } catch (err) {
        logger.error("Failed to load samples:", err);
      }
    };
    
    loadSamples();
  }, []);

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

  const handleLoadSample = async () => {
    setLoadingSample(true);
    setError(null);
    
    // Determine which sample to load
    let sampleToLoad: any = null;
    
    if (selectedSampleId) {
      sampleToLoad = availableSamples.find(s => s.id === selectedSampleId);
    } else if (availableSamples.length > 0) {
      // Fallback to first available sample if none selected
      sampleToLoad = availableSamples[0];
    }
    
    if (!sampleToLoad) {
      setError("No sample selected");
      setLoadingSample(false);
      return;
    }
    
    try {
      if (sampleToLoad.exists) {
        setFilePaths(sampleToLoad.path);
        localStorage.setItem(LAST_PATH_KEY, sampleToLoad.path);
      } else {
        setError("Sample file not extracted yet. Please restart the server.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sample file");
    } finally {
      setLoadingSample(false);
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
      // Save paths to localStorage for next time
      localStorage.setItem(LAST_PATH_KEY, filePaths);

      // Add initial progress event to show widget immediately
      setProgressEvents([{
        type: "file_selection",
        message: "Selecting files...",
        task_id: "pending",
        timestamp: new Date().toISOString(),
      }]);

      // First, select files (expands folders to file list)
      const selectResponse = await apiClient.selectFiles(paths);

      if (selectResponse.files.length === 0) {
        setError("No valid files found in the provided paths");
        setAnalyzing(false);
        return;
      }

      // Extract task ID from first progress event
      let taskIdExtracted = false;

      // Then, run analysis with progress tracking
      const response = await apiClient.analyzeWithProgress(
        selectedInsightIds,
        selectResponse.files,
        (event: ProgressEvent) => {
          setProgressEvents((prev) => [...prev, event]);
          if (!taskIdExtracted && event.task_id) {
            setCurrentTaskId(event.task_id);
            taskIdExtracted = true;
          }
        }
      );

      setAnalysisResponse(response);
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
      <main className="flex min-h-screen w-full max-w-[90%] flex-col gap-8 pb-8 px-4 mx-auto bg-background/80 backdrop-blur-sm border-x border-border">
        <div className="bg-gradient-to-r from-primary/10 via-accent/5 to-primary/10 -mx-4 px-6 py-4">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
            {t("app.title")}
          </h1>
          <p className="text-foreground/80 mt-2 font-medium">{t("app.tagline")}</p>
        </div>

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
              <textarea
                value={filePaths}
                onChange={(e) => setFilePaths(e.target.value)}
                placeholder={t("app.filePathsPlaceholder")}
                className="w-full h-[3.5rem] rounded-md border border-input bg-muted px-4 py-2 font-mono text-sm resize-y"
                rows={2}
                disabled={analyzing}
              />
              <div className="space-y-2">
                {availableSamples.length > 1 && (
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-muted-foreground whitespace-nowrap">
                      {t("app.selectSample")}:
                    </label>
                    <Select
                      value={selectedSampleId || ""}
                      onValueChange={setSelectedSampleId}
                      disabled={analyzing || loadingSample}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder={t("app.selectSamplePlaceholder")} />
                      </SelectTrigger>
                      <SelectContent>
                        {availableSamples.map((sample) => (
                          <SelectItem key={sample.id} value={sample.id}>
                            <div className="flex flex-col">
                              <span className="font-medium">{sample.name}</span>
                              {sample.description && (
                                <span className="text-xs text-muted-foreground">
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
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">
                    {t("app.filePathsHint")}
                  </p>
                  <Button
                    onClick={handleLoadSample}
                    disabled={analyzing || loadingSample || (availableSamples.length > 1 && !selectedSampleId)}
                    variant="secondary"
                    size="sm"
                    className="ml-4 whitespace-nowrap bg-gradient-to-r from-primary/10 to-accent/10 hover:from-primary/20 hover:to-accent/20 text-foreground border border-primary/30 font-bold"
                  >
                    {loadingSample ? t("common.loading") : t("app.loadSampleFile")}
                  </Button>
                </div>
              </div>
            </div>
          </section>

          {/* Insight Selection */}
          <section>
            <h2 className="text-lg font-semibold mb-4">{t("app.selectInsights")}</h2>
            <InsightList
              selectedInsightIds={selectedInsightIds}
              onSelectionChange={setSelectedInsightIds}
            />
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
                onOpenSettings={() => setSettingsOpen(true)}
              />
            </section>
          )}
        </div>
      </main>

      {/* Settings Dialog */}
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />

      {/* Status Bar with Settings Button */}
      <StatusBar onOpenSettings={() => setSettingsOpen(true)} />
    </div>
  );
}
