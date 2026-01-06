"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AnalysisResultItem } from "@/lib/api-types";

interface ResultsPanelProps {
  results: AnalysisResultItem[];
  loading?: boolean;
}

export function ResultsPanel({ results, loading }: ResultsPanelProps) {
  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground">Analyzing...</div>
    );
  }

  if (results.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Analysis Results</h2>
      <div className="space-y-4">
        {results.map((resultItem, index) => (
          <Card key={resultItem.insight_id}>
            <CardHeader>
              <CardTitle className="text-base">Insight: {resultItem.insight_id}</CardTitle>
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

