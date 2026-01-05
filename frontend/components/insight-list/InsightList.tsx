"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useInsights } from "@/hooks/use-insights";
import { InsightMetadata } from "@/lib/api-types";

interface InsightListProps {
  selectedInsightIds: string[];
  onSelectionChange: (insightIds: string[]) => void;
  disabled?: boolean;
}

export function InsightList({ selectedInsightIds, onSelectionChange, disabled }: InsightListProps) {
  const { insights, loading, error } = useInsights();

  const handleToggle = (insightId: string) => {
    if (selectedInsightIds.includes(insightId)) {
      onSelectionChange(selectedInsightIds.filter((id) => id !== insightId));
    } else {
      onSelectionChange([...selectedInsightIds, insightId]);
    }
  };

  // Group insights by folder
  const groupedInsights = useMemo(() => {
    const groups: Record<string, InsightMetadata[]> = {};
    insights.forEach((insight) => {
      const folder = insight.folder || "General";
      if (!groups[folder]) {
        groups[folder] = [];
      }
      groups[folder].push(insight);
    });
    return groups;
  }, [insights]);

  // Sort folder names (General first, then alphabetically)
  const sortedFolders = useMemo(() => {
    const folders = Object.keys(groupedInsights);
    const generalIndex = folders.indexOf("General");
    if (generalIndex > -1) {
      const general = folders.splice(generalIndex, 1)[0];
      return [general, ...folders.sort()];
    }
    return folders.sort();
  }, [groupedInsights]);

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
      <div className="overflow-y-auto max-h-[500px] pr-2 border rounded-md">
        <Accordion type="multiple" className="w-full" defaultValue={sortedFolders}>
          {sortedFolders.map((folder) => (
            <AccordionItem key={folder} value={folder} className="px-4 border-b">
              <AccordionTrigger className="text-sm font-semibold py-3">
                {folder}
                <span className="text-xs text-muted-foreground ml-2">
                  ({groupedInsights[folder].length})
                </span>
              </AccordionTrigger>
              <AccordionContent className="pb-4">
                <div className="space-y-3 pt-2">
                  {groupedInsights[folder].map((insight) => (
                    <Card key={insight.id} className="flex flex-col justify-between">
                      <CardHeader className="flex flex-row items-start gap-4 space-y-0">
                        <Checkbox
                          id={insight.id}
                          checked={selectedInsightIds.includes(insight.id)}
                          onCheckedChange={() => handleToggle(insight.id)}
                          disabled={disabled}
                          className="mt-1"
                        />
                        <div className="space-y-1 flex-1">
                          <CardTitle className="text-base">
                            <label htmlFor={insight.id} className="cursor-pointer">
                              {insight.name}
                            </label>
                          </CardTitle>
                          <CardDescription>{insight.description}</CardDescription>
                        </div>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
