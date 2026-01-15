"use client";

import { useState, useMemo, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Star } from "lucide-react";
import { useInsights } from "@/hooks/use-insights";
import { useFavorites } from "@/hooks/use-favorites";
import { InsightMetadata } from "@/lib/api-types";
import { useTranslation } from "@/lib/i18n";

interface InsightListProps {
  selectedInsightIds: string[];
  onSelectionChange: (insightIds: string[]) => void;
  disabled?: boolean;
}

const INSIGHTS_TAB_STORAGE_KEY = "lens_insights_active_tab";

export function InsightList({ selectedInsightIds, onSelectionChange, disabled }: InsightListProps) {
  const { t } = useTranslation();
  const { insights, loading, error, refresh } = useInsights();
  const { favorites, loading: favoritesLoading, toggleFavorite, isFavorite } = useFavorites();
  
  // Load active tab from localStorage on mount
  const [activeTab, setActiveTab] = useState<string>(() => {
    if (typeof window === "undefined") return "all";
    try {
      const saved = localStorage.getItem(INSIGHTS_TAB_STORAGE_KEY);
      return saved === "favorites" || saved === "all" ? saved : "all";
    } catch (error) {
      console.error("Failed to load active tab from localStorage:", error);
      return "all";
    }
  });
  
  // Save active tab to localStorage when it changes
  useEffect(() => {
    try {
      localStorage.setItem(INSIGHTS_TAB_STORAGE_KEY, activeTab);
    } catch (error) {
      console.error("Failed to save active tab to localStorage:", error);
    }
  }, [activeTab]);

  // Listen for insight refresh events from settings
  useEffect(() => {
    const handleRefresh = () => {
      refresh();
    };

    window.addEventListener('insights-refreshed', handleRefresh);
    return () => {
      window.removeEventListener('insights-refreshed', handleRefresh);
    };
  }, [refresh]);

  const handleToggle = (insightId: string) => {
    if (selectedInsightIds.includes(insightId)) {
      onSelectionChange(selectedInsightIds.filter((id) => id !== insightId));
    } else {
      onSelectionChange([...selectedInsightIds, insightId]);
    }
  };

  // Filter insights based on active tab
  const filteredInsights = useMemo(() => {
    if (activeTab === "favorites") {
      return insights.filter((insight) => isFavorite(insight.id));
    }
    return insights;
  }, [insights, activeTab, isFavorite]);

  // Group insights by folder
  const groupedInsights = useMemo(() => {
    const groups: Record<string, InsightMetadata[]> = {};
    filteredInsights.forEach((insight) => {
      const folder = insight.folder || "General";
      if (!groups[folder]) {
        groups[folder] = [];
      }
      groups[folder].push(insight);
    });
    return groups;
  }, [filteredInsights]);

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

  const handleStarClick = async (e: React.MouseEvent, insightId: string) => {
    e.stopPropagation(); // Prevent card selection
    try {
      await toggleFavorite(insightId);
    } catch (err) {
      // Error is handled by the hook
      console.error("Failed to toggle favorite:", err);
    }
  };

  const renderInsightCards = () => {
    if (sortedFolders.length === 0) {
      if (activeTab === "favorites") {
        return (
          <div className="text-center py-8 text-muted-foreground">{t("insights.noFavorites")}</div>
        );
      }
      return (
        <div className="text-center py-8 text-muted-foreground">{t("insights.noInsights")}</div>
      );
    }

    return (
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
                  const favorited = isFavorite(insight.id);
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
                      {/* Star icon - favorite indicator (top-left) */}
                      <button
                        onClick={(e) => handleStarClick(e, insight.id)}
                        className={`absolute -top-1 -left-1 w-5 h-5 rounded-full flex items-center justify-center transition-all duration-200 border-2 z-20
                          ${favorited 
                            ? 'bg-primary dark:bg-primary border-primary dark:border-primary scale-100 opacity-100' 
                            : 'bg-muted dark:bg-muted border-muted-foreground/30 dark:border-muted-foreground/30 scale-90 opacity-40 group-hover:opacity-70 group-hover:scale-100'
                          }
                          hover:scale-110 hover:opacity-100`}
                        aria-label={favorited ? "Remove from favorites" : "Add to favorites"}
                        title={favorited ? "Remove from favorites" : "Add to favorites"}
                      >
                        <Star 
                          className={`w-3 h-3 transition-colors duration-200 ${
                            favorited 
                              ? 'text-white dark:text-white fill-current' 
                              : 'text-muted-foreground dark:text-muted-foreground fill-none'
                          }`}
                          fill={favorited ? "currentColor" : "none"}
                          strokeWidth={favorited ? 0 : 2}
                        />
                      </button>

                      {/* Visual selection indicator - checkmark badge (top-right) */}
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
    );
  };

  return (
    <div className="space-y-2">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="all">{t("insights.allInsights")}</TabsTrigger>
          <TabsTrigger value="favorites">{t("insights.favorites")}</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="mt-2">
          <div className="max-h-[400px] overflow-y-auto pr-2 border rounded-md">
            {renderInsightCards()}
          </div>
        </TabsContent>
        <TabsContent value="favorites" className="mt-2">
          <div className="max-h-[400px] overflow-y-auto pr-2 border rounded-md">
            {favoritesLoading ? (
              <div className="text-center py-8 text-muted-foreground">{t("insights.loading")}</div>
            ) : (
              renderInsightCards()
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
