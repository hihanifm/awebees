"use client";

import { AlertCircle, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ErrorEvent } from "@/lib/api-types";
import { cn } from "@/lib/utils";

interface PluginErrorDialogProps {
  error: ErrorEvent | null;
  open: boolean;
  onClose: () => void;
}

export function PluginErrorDialog({ error, open, onClose }: PluginErrorDialogProps) {
  if (!error) {
    return null;
  }

  const isCritical = error.severity === "critical" || error.severity === "error";

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <AlertCircle className={cn(
              "h-6 w-6",
              isCritical ? "text-red-600 dark:text-red-400" : "text-amber-600 dark:text-amber-400"
            )} />
            <DialogTitle className={cn(
              isCritical ? "text-red-700 dark:text-red-300" : "text-amber-700 dark:text-amber-300"
            )}>
              Plugin Load Error
            </DialogTitle>
          </div>
          <DialogDescription className="pt-2">
            An error occurred while loading a plugin. This may prevent insights from being available.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Main Error Message */}
          <div className={cn(
            "rounded-lg border px-4 py-3",
            isCritical 
              ? "border-red-400 bg-red-50 dark:bg-red-950 dark:border-red-800"
              : "border-amber-400 bg-amber-50 dark:bg-amber-950 dark:border-amber-800"
          )}>
            <div className={cn(
              "font-semibold text-sm mb-2",
              isCritical 
                ? "text-red-700 dark:text-red-300"
                : "text-amber-700 dark:text-amber-300"
            )}>
              {error.message}
            </div>
            {error.details && (
              <div className={cn(
                "text-sm mt-2 whitespace-pre-wrap break-words",
                isCritical 
                  ? "text-red-600 dark:text-red-400"
                  : "text-amber-600 dark:text-amber-400"
              )}>
                {error.details}
              </div>
            )}
          </div>

          {/* Error Metadata */}
          <div className="space-y-2 text-sm">
            <div className="grid grid-cols-2 gap-4">
              {error.type && (
                <div>
                  <span className="font-semibold text-muted-foreground">Error Type:</span>
                  <div className="mt-1 font-mono text-xs">{error.type}</div>
                </div>
              )}
              {error.severity && (
                <div>
                  <span className="font-semibold text-muted-foreground">Severity:</span>
                  <div className="mt-1 font-mono text-xs capitalize">{error.severity}</div>
                </div>
              )}
            </div>

            {(error.folder || error.file || error.insight_id) && (
              <div className="pt-2 border-t">
                <div className="font-semibold text-muted-foreground mb-2">Location:</div>
                <div className="space-y-1 text-xs font-mono">
                  {error.folder && (
                    <div>
                      <span className="text-muted-foreground">Folder:</span> {error.folder}
                    </div>
                  )}
                  {error.file && (
                    <div>
                      <span className="text-muted-foreground">File:</span> {error.file}
                    </div>
                  )}
                  {error.insight_id && (
                    <div>
                      <span className="text-muted-foreground">Insight ID:</span> {error.insight_id}
                    </div>
                  )}
                </div>
              </div>
            )}

            {error.timestamp && (
              <div className="pt-2 border-t text-xs text-muted-foreground">
                <span className="font-semibold">Time:</span> {new Date(error.timestamp).toLocaleString()}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button onClick={onClose} variant="default">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
