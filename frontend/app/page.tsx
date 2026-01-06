"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { InsightList } from "@/components/insight-list/InsightList";
import { ResultsPanel } from "@/components/results-panel/ResultsPanel";
import { ProgressWidget } from "@/components/progress/ProgressWidget";
import { ErrorBanner } from "@/components/ErrorBanner";
import { apiClient } from "@/lib/api-client";
import { AnalysisResultItem, ProgressEvent, ErrorEvent } from "@/lib/api-types";

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
  const [filePaths, setFilePaths] = useState<string>("");
  const [selectedInsightIds, setSelectedInsightIds] = useState<string[]>([]);
  const [results, setResults] = useState<AnalysisResultItem[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [backendErrors, setBackendErrors] = useState<ErrorEvent[]>([]);
  const [loadingSample, setLoadingSample] = useState(false);

  // Stream backend errors on mount
  useEffect(() => {
    const streamErrors = async () => {
      try {
        await apiClient.streamErrors((error: ErrorEvent) => {
          setBackendErrors((prev) => [...prev, error]);
        });
      } catch (err) {
        console.error("Failed to stream errors:", err);
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

  const handleCancel = async () => {
    if (currentTaskId) {
      try {
        await apiClient.cancelAnalysis(currentTaskId);
        setAnalyzing(false);
      } catch (err) {
        console.error("Error cancelling analysis:", err);
      }
    }
  };

  const handleLoadSample = async () => {
    setLoadingSample(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/files/samples`);
      if (!response.ok) {
        throw new Error("Failed to load sample files");
      }
      const data = await response.json();
      
      if (data.samples && data.samples.length > 0) {
        const sample = data.samples[0]; // Get first available sample
        if (sample.exists) {
          setFilePaths(sample.path);
          localStorage.setItem(LAST_PATH_KEY, sample.path);
        } else {
          setError("Sample file not extracted yet. Please restart the server.");
        }
      } else {
        setError("No sample files available");
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
    setResults([]);
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

      setResults(response.results);
    } catch (err) {
      if (err instanceof Error && err.message === "Analysis cancelled") {
        setError("Analysis was cancelled");
      } else {
        setError(err instanceof Error ? err.message : "Failed to analyze files");
      }
    } finally {
      setAnalyzing(false);
      setCurrentTaskId(null);
    }
  };

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-orange-50/30 via-background to-amber-50/20 font-sans dark:from-orange-950/10 dark:via-background dark:to-amber-950/5">
      <main className="flex min-h-screen w-full max-w-[90%] flex-col gap-8 py-8 px-4 mx-auto bg-white/80 dark:bg-zinc-950/80 backdrop-blur-sm border-x border-orange-100/50 dark:border-orange-900/20">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight bg-gradient-to-r from-orange-600 via-amber-600 to-orange-500 bg-clip-text text-transparent dark:from-orange-400 dark:via-amber-400 dark:to-orange-300">
            Lens
          </h1>
          <p className="text-muted-foreground mt-1">A modular engine for extracting insights from messy data!</p>
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
                <h2 className="text-lg font-semibold mb-4">Enter File or Folder Paths</h2>
            <div className="space-y-2">
              <textarea
                value={filePaths}
                onChange={(e) => setFilePaths(e.target.value)}
                placeholder="Enter file or folder paths (one per line)&#10;Example:&#10;/Users/username/logs/file.log&#10;/var/log/app.log"
                className="w-full h-[3.5rem] rounded-md border border-input bg-background px-3 py-2 font-mono text-sm resize-y"
                rows={2}
                disabled={analyzing}
              />
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Enter absolute paths to log files or folders on the server (e.g., /Users/username/logs/file.log or /var/log/app.log).
                  Folders will be scanned recursively.
                </p>
                <Button
                  onClick={handleLoadSample}
                  disabled={analyzing || loadingSample}
                  variant="secondary"
                  size="sm"
                  className="ml-4 whitespace-nowrap bg-gradient-to-r from-orange-100 to-amber-100 hover:from-orange-200 hover:to-amber-200 text-orange-900 border border-orange-300/50 dark:from-orange-950 dark:to-amber-950 dark:hover:from-orange-900 dark:hover:to-amber-900 dark:text-orange-200 dark:border-orange-800/50"
                >
                  {loadingSample ? "Loading..." : "Load Sample File"}
                </Button>
              </div>
            </div>
          </section>

          {/* Insight Selection */}
          <section>
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
              className="w-full"
            >
              {analyzing ? "Analyzing..." : "Analyze Files"}
            </Button>
            {error && (
              <div className="mt-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
                <p className="text-sm text-red-600 dark:text-red-400">Error: {error}</p>
              </div>
            )}
          </section>

          {/* Results */}
          {results.length > 0 && (
            <section>
              <ResultsPanel results={results} loading={analyzing} />
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
