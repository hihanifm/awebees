"use client";

import { X, AlertCircle, AlertTriangle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ErrorEvent } from "@/lib/api-types";
import { cn } from "@/lib/utils";

interface ErrorBannerProps {
  errors: ErrorEvent[];
  onDismiss: (index: number) => void;
}

export function ErrorBanner({ errors, onDismiss }: ErrorBannerProps) {
  if (errors.length === 0) {
    return null;
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      case "error":
        return <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      case "warning":
        return <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />;
      default:
        return <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />;
    }
  };

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case "critical":
        return "border-red-500 bg-red-50 dark:bg-red-950 dark:border-red-800";
      case "error":
        return "border-red-400 bg-red-50 dark:bg-red-950 dark:border-red-800";
      case "warning":
        return "border-amber-400 bg-amber-50 dark:bg-amber-950 dark:border-amber-800";
      default:
        return "border-blue-400 bg-blue-50 dark:bg-blue-950 dark:border-blue-800";
    }
  };

  const getSeverityTextColor = (severity: string) => {
    switch (severity) {
      case "critical":
      case "error":
        return "text-red-700 dark:text-red-300";
      case "warning":
        return "text-amber-700 dark:text-amber-300";
      default:
        return "text-blue-700 dark:text-blue-300";
    }
  };

  return (
    <div className="space-y-2">
      {errors.map((error, index) => (
        <div
          key={index}
          className={cn(
            "rounded-lg border px-4 py-3 flex items-start gap-3",
            getSeverityStyles(error.severity)
          )}
        >
          <div className="mt-0.5">{getSeverityIcon(error.severity)}</div>
          <div className="flex-1 min-w-0">
            <div className={cn("font-semibold text-sm", getSeverityTextColor(error.severity))}>
              {error.message}
            </div>
            {error.details && (
              <div className={cn("text-xs mt-1", getSeverityTextColor(error.severity))}>
                {error.details}
              </div>
            )}
            <div className="text-xs mt-1 text-muted-foreground flex gap-3 flex-wrap">
              {error.folder && <span>Folder: {error.folder}</span>}
              {error.file && <span>File: {error.file}</span>}
              {error.insight_id && <span>Insight ID: {error.insight_id}</span>}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 hover:bg-black/10 dark:hover:bg-white/10"
            onClick={() => onDismiss(index)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}

