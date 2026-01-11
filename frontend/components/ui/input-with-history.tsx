"use client";

import { useState, useEffect } from "react";
import { Input, InputProps } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { saveInputHistory, getInputHistory } from "@/lib/input-history-storage";

export interface InputWithHistoryProps extends Omit<InputProps, "value" | "onChange"> {
  value: string;
  onChange: (value: string) => void;
  storageKey: string;
  historyLabel?: string;
}

export function InputWithHistory({
  value,
  onChange,
  storageKey,
  historyLabel = "Recent:",
  ...inputProps
}: InputWithHistoryProps) {
  const [history, setHistory] = useState<string[]>([]);
  const [selectedHistoryValue, setSelectedHistoryValue] = useState<string>("");

  // Load history on mount
  useEffect(() => {
    setHistory(getInputHistory(storageKey));
  }, [storageKey]);

  // Save to history when value changes (only if not empty)
  useEffect(() => {
    if (value && value.trim()) {
      saveInputHistory(storageKey, value);
      // Reload history after saving
      setHistory(getInputHistory(storageKey));
    }
  }, [value, storageKey]);

  const handleHistorySelect = (selectedValue: string) => {
    onChange(selectedValue);
    // Reset selected value after a short delay to allow Select to close
    setTimeout(() => setSelectedHistoryValue(""), 100);
  };

  return (
    <div className="space-y-2">
      {history.length > 0 && (
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground whitespace-nowrap">
            {historyLabel}
          </label>
          <Select
            value={selectedHistoryValue || undefined}
            onValueChange={handleHistorySelect}
            disabled={inputProps.disabled}
          >
            <SelectTrigger className="w-full text-left">
              <SelectValue placeholder="Select a recent value..." />
            </SelectTrigger>
            <SelectContent>
              {history.map((item) => (
                <SelectItem key={item} value={item}>
                  <span className="text-sm truncate block" title={item}>
                    {item}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
      <Input
        {...inputProps}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
