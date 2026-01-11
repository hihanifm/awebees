"use client";

import { useState, useEffect, useRef } from "react";
import { Input, InputProps } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ChevronDown, X, Trash2 } from "lucide-react";
import { saveInputHistory, getInputHistory, deleteInputHistoryItem } from "@/lib/input-history-storage";
import { cn } from "@/lib/utils";

export interface InputWithHistoryProps extends Omit<InputProps, "value" | "onChange"> {
  value: string;
  onChange: (value: string) => void;
  storageKey: string;
}

export function InputWithHistory({
  value,
  onChange,
  storageKey,
  className,
  ...inputProps
}: InputWithHistoryProps) {
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

  const handleDelete = (e: React.MouseEvent, itemToDelete: string) => {
    e.stopPropagation(); // Prevent triggering the select action
    deleteInputHistoryItem(storageKey, itemToDelete);
    setHistory(getInputHistory(storageKey));
    // Keep dropdown open after deletion
  };

  const handleToggle = () => {
    if (history.length > 0) {
      setIsOpen(!isOpen);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      saveToHistory();
      setIsOpen(false);
    }
    // Call original onKeyDown if provided
    inputProps.onKeyDown?.(e);
  };

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Input
          {...inputProps}
          className={cn(
            history.length > 0 && "pr-8",
            className
          )}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => history.length > 0 && setIsOpen(true)}
          onBlur={() => {
            // Save on blur as well (when user leaves the field)
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
            className="absolute right-0 top-0 h-full w-8 rounded-l-none hover:bg-transparent"
            onClick={handleToggle}
            disabled={inputProps.disabled}
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
            <div
              key={item}
              className="group flex items-center gap-2 px-3 py-2 hover:bg-accent first:rounded-t-md last:rounded-b-md"
            >
              <button
                type="button"
                className="flex-1 text-left text-sm hover:text-accent-foreground focus:text-accent-foreground focus:outline-none"
                onClick={() => handleHistorySelect(item)}
              >
                <span className="truncate block" title={item}>
                  {item}
                </span>
              </button>
              <button
                type="button"
                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-destructive/20 focus:bg-destructive/20 focus:outline-none transition-opacity"
                onClick={(e) => handleDelete(e, item)}
                title="Delete from history"
              >
                <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
