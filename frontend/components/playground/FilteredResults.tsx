"use client";

import { FilterResult } from "@/lib/api-types";
import { Button } from "@/components/ui/button";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

interface FilteredResultsProps {
  result: FilterResult | null;
  loading: boolean;
}

export function FilteredResults({ result, loading }: FilteredResultsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result.lines.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="border border-orange-200 dark:border-orange-800 rounded-lg p-6">
        <div className="flex items-center justify-center text-orange-600 dark:text-orange-400">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 dark:border-orange-400"></div>
          <span className="ml-3">Filtering...</span>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="border border-dashed border-orange-200 dark:border-orange-800 rounded-lg p-8 text-center">
        <p className="text-muted-foreground mb-4">No results yet. Enter a file path and ripgrep pattern above.</p>
        <div className="text-sm text-muted-foreground space-y-2">
          <p className="font-semibold">Ripgrep Pattern Examples:</p>
          <code className="block bg-muted px-3 py-2 rounded">ERROR|FATAL</code>
          <code className="block bg-muted px-3 py-2 rounded">Exception.*at\s+line</code>
          <code className="block bg-muted px-3 py-2 rounded">\b(failed|error|crash)\b</code>
        </div>
      </div>
    );
  }

  return (
    <div className="border border-orange-200 dark:border-orange-800 rounded-lg overflow-hidden">
      {/* Header with metadata */}
      <div className="bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-950/50 dark:to-amber-950/30 px-4 py-3 border-b border-orange-200 dark:border-orange-800 flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-orange-900 dark:text-orange-200 font-medium">
            {result.total_count} {result.total_count === 1 ? "line" : "lines"} found
          </span>
          <span className="text-muted-foreground">
            {result.execution_time.toFixed(3)}s
          </span>
          {result.truncated && (
            <span className="text-amber-700 dark:text-amber-400 font-medium">
              (Truncated to first 1000 lines)
            </span>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="text-orange-700 dark:text-orange-300 hover:bg-orange-100 dark:hover:bg-orange-900/30"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 mr-2" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="h-4 w-4 mr-2" />
              Copy
            </>
          )}
        </Button>
      </div>

      {/* Command display */}
      <div className="bg-muted px-4 py-2 border-b border-orange-200 dark:border-orange-800">
        <code className="text-xs text-muted-foreground font-mono">
          $ {result.ripgrep_command}
        </code>
      </div>

      {/* Results */}
      <div className="bg-orange-50/50 dark:bg-orange-950/20 overflow-auto max-h-96 border-t border-orange-200 dark:border-orange-800">
        <pre className="p-4 text-sm font-mono text-zinc-900 dark:text-zinc-200">
          {result.lines.map((line, index) => (
            <div key={index} className="flex hover:bg-orange-100/30 dark:hover:bg-orange-900/20">
              <span className="text-orange-600 dark:text-orange-500 select-none mr-4 text-right w-12 flex-shrink-0 font-semibold">
                {index + 1}
              </span>
              <span className="flex-1">{line}</span>
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}

