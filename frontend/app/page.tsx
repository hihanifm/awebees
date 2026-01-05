"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { InsightList } from "@/components/insight-list/InsightList";
import { ResultsPanel } from "@/components/results-panel/ResultsPanel";
import { ProgressWidget } from "@/components/progress/ProgressWidget";
import { apiClient } from "@/lib/api-client";
import { AnalysisResultItem, ProgressEvent } from "@/lib/api-types";

const LAST_PATH_KEY = "lens_last_file_paths";

export default function Home() {
  const [filePaths, setFilePaths] = useState<string>("");
  const [selectedInsightIds, setSelectedInsightIds] = useState<string[]>([]);
  const [results, setResults] = useState<AnalysisResultItem[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

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

  const handleAnalyze = async () => {
    if (selectedInsightIds.length === 0) {
      setError("Please select at least one insight");
      return;
    }

    const paths = filePaths
      .split("\n")
      .map((p) => p.trim())
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
    <div className="flex min-h-screen bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-5xl flex-col gap-8 py-8 px-4 mx-auto bg-white dark:bg-black">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
            Lens
          </h1>
          <p className="text-muted-foreground mt-1">A modular engine for extracting insight from data!</p>
        </div>

        <div className="space-y-8">
              {/* File Selection */}
              <section>
                <h2 className="text-lg font-semibold mb-4">Enter File or Folder Paths</h2>
            <div className="space-y-2">
              <textarea
                value={filePaths}
                onChange={(e) => setFilePaths(e.target.value)}
                placeholder="Enter file or folder paths (one per line)&#10;Example:&#10;/Users/username/logs/file.log&#10;/var/log/app.log"
                className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
                disabled={analyzing}
              />
              <p className="text-xs text-muted-foreground">
                Enter absolute paths to log files or folders on the server (e.g., /Users/username/logs/file.log or /var/log/app.log).
                Folders will be scanned recursively. The last used paths will be prefilled automatically.
              </p>
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
