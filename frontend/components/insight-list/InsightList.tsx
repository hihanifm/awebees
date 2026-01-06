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
      <div className="overflow-y-auto max-h-[600px] pr-2 border rounded-md">
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
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 pt-2">
                  {groupedInsights[folder].map((insight) => (
                    <Card 
                      key={insight.id} 
                      className="group relative isolate flex flex-col items-center justify-center p-4 
                        hover:shadow-lg hover:shadow-orange-200/50 dark:hover:shadow-orange-900/30
                        hover:z-10 
                        hover:border-orange-400/60 
                        hover:bg-gradient-to-br hover:from-orange-50 hover:to-amber-50 
                        dark:hover:from-orange-950/50 dark:hover:to-amber-950/50 
                        transition-all duration-200 
                        cursor-pointer min-h-[100px]"
                      title={insight.description}
                      onClick={() => handleToggle(insight.id)}
                    >
                      <Checkbox
                        id={insight.id}
                        checked={selectedInsightIds.includes(insight.id)}
                        onCheckedChange={() => handleToggle(insight.id)}
                        disabled={disabled}
                        className="absolute top-3 left-3 group-hover:border-orange-500 group-hover:scale-110 transition-all duration-200"
                      />
                      <label 
                        htmlFor={insight.id} 
                        className="text-sm font-medium text-center mt-2 cursor-pointer select-none leading-tight px-6
                          group-hover:text-orange-700 dark:group-hover:text-orange-300
                          transition-colors duration-200"
                      >
                        {insight.name}
                      </label>
                      
                      {/* Enhanced Tooltip with warm styling */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 w-64 p-3 
                        bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950 dark:to-amber-950
                        border-2 border-orange-300/50 dark:border-orange-700/50 
                        rounded-lg shadow-xl shadow-orange-200/30 dark:shadow-orange-900/50">
                        <p className="text-xs text-foreground">{insight.description}</p>
                        <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-8 border-transparent border-t-orange-300/50 dark:border-t-orange-700/50"></div>
                      </div>
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
