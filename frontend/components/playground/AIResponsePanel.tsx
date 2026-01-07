"use client";

import { Button } from "@/components/ui/button";
import { Copy, Check, Loader2 } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

interface AIResponsePanelProps {
  response: string;
  streaming: boolean;
  error: string | null;
}

export function AIResponsePanel({ response, streaming, error }: AIResponsePanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (error) {
    return (
      <div className="border border-red-300 dark:border-red-800 rounded-lg p-6 bg-red-50 dark:bg-red-950/20">
        <div className="flex items-start gap-3">
          <span className="text-red-600 dark:text-red-400 font-semibold">Error:</span>
          <p className="text-red-700 dark:text-red-300 flex-1">{error}</p>
        </div>
      </div>
    );
  }

  if (streaming && !response) {
    return (
      <div className="border border-orange-200 dark:border-orange-800 rounded-lg p-6">
        <div className="flex items-center justify-center text-orange-600 dark:text-orange-400">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-3">AI is analyzing...</span>
        </div>
      </div>
    );
  }

  if (!response && !streaming) {
    return (
      <div className="border border-dashed border-orange-200 dark:border-orange-800 rounded-lg p-8 text-center">
        <p className="text-muted-foreground mb-4">
          No AI response yet. Configure prompts and click &quot;Analyze with AI&quot; above.
        </p>
        <div className="text-sm text-muted-foreground space-y-2">
          <p className="font-semibold">AI will help you:</p>
          <ul className="text-left max-w-md mx-auto space-y-1">
            <li>• Summarize filtered results</li>
            <li>• Explain patterns and trends</li>
            <li>• Provide actionable recommendations</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="border border-orange-200 dark:border-orange-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-950/50 dark:to-amber-950/30 px-4 py-3 border-b border-orange-200 dark:border-orange-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-orange-900 dark:text-orange-200 font-medium">
            AI Analysis
          </span>
          {streaming && (
            <span className="flex items-center text-sm text-orange-700 dark:text-orange-300">
              <Loader2 className="h-3 w-3 animate-spin mr-1" />
              Streaming...
            </span>
          )}
        </div>
        {response && (
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
        )}
      </div>

      {/* Response content */}
      <div className="p-6 bg-white dark:bg-zinc-950 overflow-auto max-h-96">
        <div className="prose dark:prose-invert max-w-none">
          <ReactMarkdown>{response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

