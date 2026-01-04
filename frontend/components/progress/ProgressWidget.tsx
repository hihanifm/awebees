"use client";

import { ProgressEvent } from "@/lib/api-types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProgressWidgetProps {
  events: ProgressEvent[];
  currentTaskId: string | null;
  onCancel: () => void;
}

export function ProgressWidget({ events, currentTaskId, onCancel }: ProgressWidgetProps) {
  if (!currentTaskId && events.length === 0) {
    return null;
  }

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
      return "Complete";
    }
    if (isCancelled) {
      return "Cancelled";
    }
    if (isError) {
      return "Error";
    }
    return "In Progress";
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
            Analysis Progress - {getStatusText()}
          </CardTitle>
          {!isComplete && !isCancelled && !isError && currentTaskId && (
            <Button
              variant="outline"
              size="sm"
              onClick={onCancel}
              className="flex items-center gap-1"
            >
              <X className="h-4 w-4" />
              Cancel
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* Current Status */}
          <div className="font-medium text-sm">
            {latestEvent?.message || "Starting analysis..."}
          </div>

          {/* Current Insight */}
          {currentInsightEvent && currentInsightEvent.type === "insight_start" && (
            <div className="text-sm text-muted-foreground">
              Running: {currentInsightEvent.insight_id}
            </div>
          )}

          {/* Event History (last 3 events) */}
          {events.length > 0 && (
            <div className="mt-4 space-y-1">
              <div className="text-xs font-semibold text-muted-foreground mb-2">
                Recent Activity:
              </div>
              <div className="space-y-1 max-h-24 overflow-y-auto">
                {events.slice(-3).map((event, index) => (
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
                        : "text-muted-foreground"
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

