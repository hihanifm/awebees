"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { InsightList } from "@/components/insight-list/InsightList";
import { ResultsPanel } from "@/components/results-panel/ResultsPanel";
import { apiClient } from "@/lib/api-client";
import { AnalysisResultItem } from "@/lib/api-types";

export default function Home() {
  const [filePaths, setFilePaths] = useState<string>("");
  const [selectedInsightIds, setSelectedInsightIds] = useState<string[]>([]);
  const [results, setResults] = useState<AnalysisResultItem[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

    try {
      // First, select files (expands folders to file list)
      const selectResponse = await apiClient.selectFiles(paths);
      
      if (selectResponse.files.length === 0) {
        setError("No valid files found in the provided paths");
        setAnalyzing(false);
        return;
      }

      // Then, run analysis
      const response = await apiClient.analyze(selectedInsightIds, selectResponse.files);
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze files");
    } finally {
      setAnalyzing(false);
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
            <h2 className="text-xl font-semibold mb-4">1. Enter File or Folder Paths</h2>
            <div className="space-y-2">
              <textarea
                value={filePaths}
                onChange={(e) => setFilePaths(e.target.value)}
                placeholder="Enter file or folder paths (one per line)&#10;Example:&#10;/path/to/logfile.log&#10;/path/to/logs/folder"
                className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Enter absolute paths to log files or folders on the server. Folders will be scanned recursively.
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
