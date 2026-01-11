"use client";

import { useState, useEffect, useRef } from "react";
import { Input, InputProps } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ChevronDown, X } from "lucide-react";
import { saveInputHistory, getInputHistory } from "@/lib/input-history-storage";
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
