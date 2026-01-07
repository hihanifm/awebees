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
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6 gap-4 pt-2">
                  {groupedInsights[folder].map((insight) => {
                    const isSelected = selectedInsightIds.includes(insight.id);
                    return (
                      <Card 
                        key={insight.id} 
                        className={`group relative isolate flex flex-col items-center justify-center p-3
                          ${isSelected 
                            ? 'bg-gradient-to-br from-orange-50 via-amber-50/50 to-orange-50 dark:from-orange-950/20 dark:via-amber-950/15 dark:to-orange-950/20 border-[2px] border-orange-400 dark:border-orange-500 shadow-md shadow-orange-200/40 dark:shadow-orange-900/40' 
                            : 'bg-gradient-to-br from-orange-50/40 via-amber-50/30 to-orange-50/40 dark:from-zinc-800 dark:via-zinc-850 dark:to-zinc-800 border-[2px] border-orange-200 dark:border-zinc-600 shadow-md shadow-orange-100/40 dark:shadow-zinc-900/40'
                          }
                          hover:shadow-xl hover:shadow-orange-300/50 dark:hover:shadow-orange-800/50
                          hover:z-10 
                          hover:border-orange-400 dark:hover:border-orange-400
                          hover:scale-105
                          ${!isSelected && 'hover:from-orange-100/60 hover:via-amber-100/50 hover:to-orange-100/60 dark:hover:from-zinc-750 dark:hover:via-zinc-800 dark:hover:to-zinc-750'}
                          transition-all duration-200 
                          cursor-pointer min-h-[80px] rounded-lg overflow-visible`}
                        title={insight.description}
                        onClick={() => handleToggle(insight.id)}
                      >
                        {/* Visual selection indicator - checkmark badge */}
                        <div className={`absolute -top-1.5 -right-1.5 w-6 h-6 rounded-full flex items-center justify-center transition-all duration-200 border-2 
                          ${isSelected 
                            ? 'bg-orange-500 dark:bg-orange-500 border-orange-600 dark:border-orange-600 scale-100' 
                            : 'bg-zinc-200 dark:bg-zinc-700 border-zinc-300 dark:border-zinc-600 scale-90 opacity-40 group-hover:opacity-70'
                          }`}>
                          {isSelected && (
                            <svg className="w-3.5 h-3.5 text-white dark:text-white" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" viewBox="0 0 24 24" stroke="currentColor">
                              <path d="M5 13l4 4L19 7"></path>
                            </svg>
                          )}
                        </div>
                        
                        <Checkbox
                          id={insight.id}
                          checked={isSelected}
                          onCheckedChange={() => handleToggle(insight.id)}
                          disabled={disabled}
                          className="sr-only"
                        />
                        
                        <label 
                          htmlFor={insight.id} 
                          className={`text-sm font-bold text-center cursor-pointer select-none leading-snug px-2
                            ${isSelected 
                              ? 'text-orange-800 dark:text-orange-200' 
                              : 'text-orange-800/80 dark:text-orange-200/70'
                            }
                            group-hover:text-orange-900 dark:group-hover:text-orange-100
                            transition-colors duration-200`}
                        >
                          {insight.name}
                        </label>
                        
                        {/* Enhanced Tooltip */}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 hidden group-hover:block z-50 w-72 p-4 
                          bg-white dark:bg-zinc-800
                          border-2 border-orange-400 dark:border-orange-500 
                          rounded-lg shadow-2xl shadow-orange-300/50 dark:shadow-orange-900/70">
                          <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">{insight.description}</p>
                          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[2px] border-[10px] border-transparent border-t-orange-400 dark:border-t-orange-500"></div>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
