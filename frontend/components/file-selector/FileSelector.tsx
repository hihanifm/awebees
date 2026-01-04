"use client";

import { Button } from "@/components/ui/button";
import { useFileSelector } from "@/hooks/use-file-selector";
import { X } from "lucide-react";

export function FileSelector() {
  const { selectedFiles, error, handleFileSelect, removeFile } = useFileSelector();

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center gap-4">
        <label>
          <input
            type="file"
            multiple
            className="hidden"
            onChange={(e) => handleFileSelect(e.target.files)}
            accept=".log,.txt,.logcat"
          />
          <Button type="button" asChild>
            <span>Select Log Files</span>
          </Button>
        </label>
        {selectedFiles.length > 0 && (
          <span className="text-sm text-muted-foreground">
            {selectedFiles.length} file{selectedFiles.length !== 1 ? "s" : ""} selected
          </span>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {selectedFiles.length > 0 && (
        <div className="rounded-lg border border-border bg-background p-4">
          <ul className="space-y-2">
            {selectedFiles.map((selectedFile, index) => (
              <li
                key={index}
                className="flex items-center justify-between rounded-md border border-border bg-muted px-3 py-2"
              >
                <span className="text-sm font-mono">{selectedFile.path}</span>
                <button
                  onClick={() => removeFile(index)}
                  className="text-muted-foreground hover:text-foreground"
                  aria-label={`Remove ${selectedFile.path}`}
                >
                  <X className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Note: This is a basic file selector. For local file paths, the backend API expects absolute paths on the server.
      </p>
    </div>
  );
}

