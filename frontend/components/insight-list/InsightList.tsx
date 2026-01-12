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
import { useTranslation } from "@/lib/i18n";

interface InsightListProps {
  selectedInsightIds: string[];
  onSelectionChange: (insightIds: string[]) => void;
  disabled?: boolean;
}

export function InsightList({ selectedInsightIds, onSelectionChange, disabled }: InsightListProps) {
  const { t } = useTranslation();
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
      <div className="text-center py-8 text-muted-foreground">{t("insights.loading")}</div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
        <p className="text-sm text-red-600 dark:text-red-400">{t("common.error")}: {error}</p>
      </div>
    );
  }

  if (insights.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">{t("insights.noInsights")}</div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="h-[400px] overflow-y-auto pr-2 border rounded-md">
        <Accordion type="multiple" className="w-full" defaultValue={sortedFolders.slice(0, 3)}>
          {sortedFolders.map((folder) => (
            <AccordionItem key={folder} value={folder} className="px-3 border-b">
              <AccordionTrigger className="text-sm font-semibold py-2">
                {folder}
                <span className="text-xs text-muted-foreground ml-2">
                  ({groupedInsights[folder].length})
                </span>
              </AccordionTrigger>
              <AccordionContent className="pb-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6 gap-2 pt-1">
                  {groupedInsights[folder].map((insight) => {
                    const isSelected = selectedInsightIds.includes(insight.id);
                    return (
                      <Card 
                        key={insight.id} 
                        className={`group relative isolate flex flex-col items-center justify-center p-2
                          ${isSelected 
                            ? 'bg-gradient-to-br from-primary/10 via-primary/5 to-primary/10 dark:from-primary/20 dark:via-primary/15 dark:to-primary/20 border-[2px] border-primary dark:border-primary shadow-md shadow-primary/20 dark:shadow-primary/20' 
                            : 'bg-gradient-to-br from-primary/5 via-primary/3 to-primary/5 dark:from-muted dark:via-muted dark:to-muted border-[2px] border-primary/30 dark:border-muted-foreground/20 shadow-md shadow-primary/10 dark:shadow-primary/10'
                          }
                          hover:shadow-xl hover:shadow-primary/30 dark:hover:shadow-primary/30
                          hover:z-10 
                          hover:border-primary dark:hover:border-primary
                          hover:scale-105
                          ${!isSelected && 'hover:from-primary/10 hover:via-primary/5 hover:to-primary/10 dark:hover:from-muted dark:hover:via-muted dark:hover:to-muted'}
                          transition-all duration-200 
                          cursor-pointer min-h-[60px] rounded-lg overflow-visible`}
                        title={insight.description}
                        onClick={() => handleToggle(insight.id)}
                      >
                        {/* Visual selection indicator - checkmark badge */}
                        <div className={`absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center transition-all duration-200 border-2 
                          ${isSelected 
                            ? 'bg-primary dark:bg-primary border-primary dark:border-primary scale-100' 
                            : 'bg-muted dark:bg-muted border-muted-foreground/30 dark:border-muted-foreground/30 scale-90 opacity-40 group-hover:opacity-70'
                          }`}>
                          {isSelected && (
                            <svg className="w-3 h-3 text-white dark:text-white" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" viewBox="0 0 24 24" stroke="currentColor">
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
                        
                        <div 
                          className={`text-sm font-bold text-center cursor-pointer select-none leading-tight px-1 pointer-events-none
                            ${isSelected 
                              ? 'text-primary dark:text-primary-foreground' 
                              : 'text-foreground/80 dark:text-foreground/70'
                            }
                            group-hover:text-foreground dark:group-hover:text-foreground
                            transition-colors duration-200`}
                        >
                          {insight.name}
                        </div>
                        
                        {/* Enhanced Tooltip */}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 w-64 p-3 
                          bg-popover dark:bg-popover
                          border-2 border-primary dark:border-primary 
                          rounded-lg shadow-2xl shadow-primary/30 dark:shadow-primary/30">
                          <p className="text-xs text-popover-foreground dark:text-popover-foreground leading-relaxed">{insight.description}</p>
                          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[2px] border-[8px] border-transparent border-t-primary dark:border-t-primary"></div>
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
