"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { useInsights } from "@/hooks/use-insights";
import { InsightMetadata } from "@/lib/api-types";

interface InsightListProps {
  selectedInsightIds: string[];
  onSelectionChange: (insightIds: string[]) => void;
}

export function InsightList({ selectedInsightIds, onSelectionChange }: InsightListProps) {
  const { insights, loading, error } = useInsights();

  const handleToggle = (insightId: string) => {
    if (selectedInsightIds.includes(insightId)) {
      onSelectionChange(selectedInsightIds.filter((id) => id !== insightId));
    } else {
      onSelectionChange([...selectedInsightIds, insightId]);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground">Loading insights...</div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
        <p className="text-sm text-red-600 dark:text-red-400">Error: {error}</p>
      </div>
    );
  }

  if (insights.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">No insights available</div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Available Insights</h2>
      <div className="overflow-y-auto max-h-[500px] pr-2 space-y-4 border rounded-md p-4">
        {insights.map((insight) => (
          <Card key={insight.id}>
            <CardHeader className="pb-3">
              <div className="flex items-center space-x-3">
                <Checkbox
                  id={insight.id}
                  checked={selectedInsightIds.includes(insight.id)}
                  onCheckedChange={() => handleToggle(insight.id)}
                />
                <div className="flex-1">
                  <CardTitle className="text-base">{insight.name}</CardTitle>
                  <CardDescription className="mt-1">
                    {insight.description}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}

