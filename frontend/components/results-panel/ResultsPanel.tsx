"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AnalysisResponse } from "@/lib/api-types";

interface ResultsPanelProps {
  analysisResponse: AnalysisResponse;
  loading?: boolean;
}

export function ResultsPanel({ analysisResponse, loading }: ResultsPanelProps) {
  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground">Analyzing...</div>
    );
  }

  const { results, total_time, insights_count } = analysisResponse;

  if (results.length === 0) {
    return null;
  }

  const formatTime = (seconds: number): string => {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Analysis Results</h2>
      
      {/* Statistics Card */}
      <Card className="bg-gradient-to-br from-orange-50 via-amber-50 to-orange-50 dark:from-orange-950/30 dark:via-amber-950/20 dark:to-orange-950/30 border-2 border-orange-200 dark:border-orange-800/50">
        <CardHeader>
          <CardTitle className="text-base text-orange-900 dark:text-orange-100">Analysis Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">Insights Run</span>
              <span className="text-2xl font-bold text-orange-700 dark:text-orange-300">{insights_count}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">Total Time</span>
              <span className="text-2xl font-bold text-orange-700 dark:text-orange-300">{formatTime(total_time)}</span>
            </div>
            <div className="flex flex-col sm:col-span-1">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">Individual Times</span>
              <div className="text-xs space-y-1 mt-1">
                {results.map((resultItem) => (
                  <div key={resultItem.insight_id} className="flex justify-between items-center">
                    <span className="text-orange-800 dark:text-orange-200 truncate mr-2 max-w-[150px]" title={resultItem.insight_id}>
                      {resultItem.insight_id}
                    </span>
                    <span className="font-semibold text-orange-700 dark:text-orange-300">
                      {formatTime(resultItem.execution_time)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        {results.map((resultItem, index) => (
          <Card key={resultItem.insight_id}>
            <CardHeader>
              <CardTitle className="text-base flex justify-between items-center">
                <span>Insight: {resultItem.insight_id}</span>
                <span className="text-xs font-normal text-muted-foreground">
                  {formatTime(resultItem.execution_time)}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {resultItem.result.result_type === "text" && (
                <pre className="whitespace-pre-wrap rounded-md border border-border bg-muted p-4 font-mono text-sm overflow-x-auto overflow-y-auto max-h-[600px]">
                  {resultItem.result.content}
                </pre>
              )}
              {resultItem.result.result_type === "file" && (
                <div className="text-sm text-muted-foreground">
                  File: {resultItem.result.content}
                </div>
              )}
              {resultItem.result.result_type === "chart_data" && (
                <div className="text-sm text-muted-foreground">
                  Chart data (JSON): <pre className="mt-2 whitespace-pre-wrap rounded-md border border-border bg-muted p-4 font-mono text-xs overflow-x-auto">{resultItem.result.content}</pre>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

