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
      <div className="border border-primary/20 rounded-lg p-6">
        <div className="flex items-center justify-center text-primary">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-3">Filtering...</span>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="border border-dashed border-primary/20 rounded-lg p-8 text-center">
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
    <div className="border border-primary/20 rounded-lg overflow-hidden">
      {/* Header with metadata */}
      <div className="bg-gradient-to-r from-primary/10 to-accent/10 px-4 py-3 border-b border-primary/20 flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-foreground font-medium">
            {result.total_count} {result.total_count === 1 ? "line" : "lines"} found
          </span>
          <span className="text-muted-foreground">
            {result.execution_time.toFixed(3)}s
          </span>
          {result.truncated && (
            <span className="text-accent font-medium">
              (Truncated to first {result.lines.length} of {result.total_count} lines)
            </span>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="text-primary hover:bg-primary/10"
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
      <div className="bg-muted px-4 py-2 border-b border-primary/20">
        <code className="text-xs text-muted-foreground font-mono">
          $ {result.ripgrep_command}
        </code>
      </div>

      {/* Results */}
      <div className="bg-primary/5 overflow-auto max-h-96 border-t border-primary/20">
        <pre className="p-4 text-sm font-mono text-foreground">
          {result.lines.map((line, index) => (
            <div key={index} className="flex hover:bg-primary/10">
              <span className="text-primary select-none mr-4 text-right w-12 flex-shrink-0 font-semibold">
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

