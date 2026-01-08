"use client";

import { ProgressEvent } from "@/lib/api-types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

interface ProgressWidgetProps {
  events: ProgressEvent[];
  currentTaskId: string | null;
  onCancel: () => void;
}

export function ProgressWidget({ events, currentTaskId, onCancel }: ProgressWidgetProps) {
  const { t } = useTranslation();
  const latestEvent = events[events.length - 1];
  const isComplete = latestEvent?.type === "analysis_complete" || latestEvent?.type === "result";
  const isCancelled = latestEvent?.type === "cancelled";
  const isError = latestEvent?.type === "error";

  const getStatusIcon = () => {
    if (isComplete) {
      return <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />;
    }
    if (isCancelled || isError) {
      return <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
    }
    return <Loader2 className="h-5 w-5 animate-spin text-blue-600 dark:text-blue-400" />;
  };

  const getStatusText = () => {
    if (isComplete) {
      return t("progress.complete");
    }
    if (isCancelled) {
      return t("progress.cancelled");
    }
    if (isError) {
      return t("progress.error");
    }
    return t("progress.inProgress");
  };

  // Get current insight being processed
  const currentInsightEvent = events
    .slice()
    .reverse()
    .find((e) => e.type === "insight_start" || e.type === "insight_complete");

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            {getStatusIcon()}
            {t("progress.analysisProgress")} - {getStatusText()}
          </CardTitle>
          {!isComplete && !isCancelled && !isError && currentTaskId && (
            <Button
              variant="outline"
              size="sm"
              onClick={onCancel}
              className="flex items-center gap-1 font-bold"
            >
              <X className="h-4 w-4" />
              {t("common.cancel")}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* Current Status */}
          <div className="font-medium text-sm">
            {latestEvent?.message || t("progress.startingAnalysis")}
          </div>

          {/* File Progress Info */}
          {latestEvent && (latestEvent.type === "file_open" || latestEvent.type === "insight_progress") && (
            <div className="text-xs text-muted-foreground space-y-1">
              {latestEvent.file_path && (
                <div>{t("progress.file")}: {latestEvent.file_path.split("/").pop()}</div>
              )}
              {latestEvent.file_index && latestEvent.total_files && (
                <div>{t("progress.progress")}: {t("progress.file")} {latestEvent.file_index} {t("progress.of")} {latestEvent.total_files}</div>
              )}
              {latestEvent.lines_processed != null && (
                <div>{t("progress.linesProcessed")}: {latestEvent.lines_processed.toLocaleString()}</div>
              )}
              {latestEvent.file_size_mb != null && (
                <div>{t("progress.fileSize")}: {latestEvent.file_size_mb.toFixed(2)} MB</div>
              )}
            </div>
          )}

          {/* Current Insight */}
          {currentInsightEvent && currentInsightEvent.type === "insight_start" && (
            <div className="text-sm text-muted-foreground">
              {t("progress.running")}: {currentInsightEvent.insight_id}
            </div>
          )}

          {/* Event History (all events, scrollable) */}
          {events.length > 0 && (
            <div className="mt-4 space-y-1">
              <div className="text-xs font-semibold text-muted-foreground mb-2">
                {t("progress.activityHistory")} ({events.length} {t("progress.events")}):
              </div>
              <div className="space-y-1 max-h-64 overflow-y-auto border rounded-md p-4 bg-muted">
                {events.map((event, index) => (
                  <div
                    key={index}
                    className={cn(
                      "text-xs font-mono",
                      event.type === "error"
                        ? "text-red-600 dark:text-red-400"
                        : event.type === "cancelled"
                        ? "text-orange-600 dark:text-orange-400"
                        : event.type === "analysis_complete" || event.type === "result"
                        ? "text-green-600 dark:text-green-400"
                        : "text-foreground"
                    )}
                  >
                    [{event.type}] {event.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

