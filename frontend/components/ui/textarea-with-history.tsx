"use client";

import { useState, useEffect, useRef } from "react";
import { Textarea, TextareaProps } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";
import { saveInputHistory, getInputHistory } from "@/lib/input-history-storage";
import { cn } from "@/lib/utils";

export interface TextareaWithHistoryProps extends Omit<TextareaProps, "value" | "onChange"> {
  value: string;
  onChange: (value: string) => void;
  storageKey: string;
}

export function TextareaWithHistory({
  value,
  onChange,
  storageKey,
  className,
  ...textareaProps
}: TextareaWithHistoryProps) {
  const [history, setHistory] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load history on mount
  useEffect(() => {
    setHistory(getInputHistory(storageKey));
  }, [storageKey]);

  const saveToHistory = () => {
    if (value && value.trim()) {
      saveInputHistory(storageKey, value);
      // Reload history after saving
      setHistory(getInputHistory(storageKey));
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  const handleHistorySelect = (selectedValue: string) => {
    onChange(selectedValue);
    setIsOpen(false);
  };

  const handleToggle = () => {
    if (history.length > 0) {
      setIsOpen(!isOpen);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Textarea
          {...textareaProps}
          className={cn(
            history.length > 0 && "pr-8",
            className
          )}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => history.length > 0 && setIsOpen(true)}
          onBlur={() => {
            // Save on blur (when user leaves the field)
            saveToHistory();
            // Close dropdown after a delay to allow clicking on items
            setTimeout(() => setIsOpen(false), 200);
          }}
        />
        {history.length > 0 && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-2 top-2 h-8 w-8 rounded-md hover:bg-accent"
            onClick={handleToggle}
            disabled={textareaProps.disabled}
          >
            <ChevronDown className={cn(
              "h-4 w-4 text-muted-foreground transition-transform",
              isOpen && "rotate-180"
            )} />
          </Button>
        )}
      </div>
      {isOpen && history.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-popover border border-input rounded-md shadow-md max-h-60 overflow-auto">
          {history.map((item) => (
            <button
              key={item}
              type="button"
              className="w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none first:rounded-t-md last:rounded-b-md"
              onClick={() => handleHistorySelect(item)}
            >
              <span className="truncate block" title={item}>
                {item}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
