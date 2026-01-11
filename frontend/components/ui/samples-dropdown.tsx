"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Sample {
  id: string;
  name: string;
  path: string;
  description?: string;
  exists?: boolean;
}

export interface SamplesDropdownProps {
  samples: Sample[];
  value?: string | null;
  onSelect: (sample: Sample) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function SamplesDropdown({
  samples,
  value,
  onSelect,
  disabled = false,
  placeholder = "Select a sample...",
}: SamplesDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedSample = samples.find((s) => s.id === value);

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

  const handleSelect = (sample: Sample) => {
    onSelect(sample);
    setIsOpen(false);
  };

  const handleToggle = () => {
    if (!disabled && samples.length > 0) {
      setIsOpen(!isOpen);
    }
  };

  if (samples.length === 0) {
    return null;
  }

  return (
    <div ref={containerRef} className="relative w-full">
      <Button
        type="button"
        variant="outline"
        className="w-full justify-between"
        onClick={handleToggle}
        disabled={disabled}
      >
        <span className="truncate text-left">
          {selectedSample ? selectedSample.name : placeholder}
        </span>
        <ChevronDown className={cn(
          "h-4 w-4 ml-2 shrink-0 text-muted-foreground transition-transform",
          isOpen && "rotate-180"
        )} />
      </Button>
      {isOpen && samples.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-popover border border-input rounded-md shadow-md max-h-60 overflow-auto">
          {samples.map((sample) => (
            <button
              key={sample.id}
              type="button"
              className="w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none first:rounded-t-md last:rounded-b-md"
              onClick={() => handleSelect(sample)}
              disabled={disabled}
            >
              <div className="flex flex-col items-start">
                <span className="font-medium truncate block w-full" title={sample.name}>
                  {sample.name}
                </span>
                {sample.description && (
                  <span className="text-xs text-muted-foreground truncate block w-full" title={sample.description}>
                    {sample.description}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
