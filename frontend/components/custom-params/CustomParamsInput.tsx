"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface KeyValuePair {
  key: string;
  value: string;
  id: string;
}

interface CustomParamsInputProps {
  value?: Record<string, any>;
  onChange?: (params: Record<string, any> | undefined) => void;
}

export function CustomParamsInput({ value, onChange }: CustomParamsInputProps) {
  const [pairs, setPairs] = useState<KeyValuePair[]>(() => {
    if (!value) return [];
    return Object.entries(value).map(([key, val], index) => ({
      id: `pair-${index}`,
      key,
      value: typeof val === "string" ? val : JSON.stringify(val),
    }));
  });

  const addPair = () => {
    const newPair: KeyValuePair = {
      id: `pair-${Date.now()}`,
      key: "",
      value: "",
    };
    const updated = [...pairs, newPair];
    setPairs(updated);
    notifyChange(updated);
  };

  const removePair = (id: string) => {
    const updated = pairs.filter((p) => p.id !== id);
    setPairs(updated);
    notifyChange(updated);
  };

  const updatePair = (id: string, field: "key" | "value", newValue: string) => {
    const updated = pairs.map((p) => (p.id === id ? { ...p, [field]: newValue } : p));
    setPairs(updated);
    notifyChange(updated);
  };

  const notifyChange = (updatedPairs: KeyValuePair[]) => {
    if (!onChange) return;

    const validPairs = updatedPairs.filter((p) => p.key.trim() !== "");
    if (validPairs.length === 0) {
      onChange(undefined);
      return;
    }

    const params: Record<string, any> = {};
    for (const pair of validPairs) {
      const key = pair.key.trim();
      if (key) {
        // Try to parse as JSON, fallback to string
        try {
          params[key] = JSON.parse(pair.value);
        } catch {
          params[key] = pair.value;
        }
      }
    }
    onChange(Object.keys(params).length > 0 ? params : undefined);
  };

  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="custom-params">
        <AccordionTrigger className="text-sm font-medium">
          Custom Parameters (Optional)
        </AccordionTrigger>
        <AccordionContent>
          <div className="space-y-4 p-4 border rounded-md bg-muted/50">
            <div className="text-sm text-muted-foreground">
              Add custom key-value parameters to pass to insights. Values can be strings, numbers,
              or JSON arrays/objects.
            </div>

            <div className="space-y-2">
              {pairs.map((pair) => (
                <div key={pair.id} className="flex gap-2 items-start">
                  <div className="flex-1 grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <Label htmlFor={`key-${pair.id}`} className="text-xs">
                        Key
                      </Label>
                      <Input
                        id={`key-${pair.id}`}
                        placeholder="e.g., android_package_name"
                        value={pair.key}
                        onChange={(e) => updatePair(pair.id, "key", e.target.value)}
                        className="h-8"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor={`value-${pair.id}`} className="text-xs">
                        Value
                      </Label>
                      <Input
                        id={`value-${pair.id}`}
                        placeholder="e.g., com.example.app or [1, 2, 3]"
                        value={pair.value}
                        onChange={(e) => updatePair(pair.id, "value", e.target.value)}
                        className="h-8"
                      />
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removePair(pair.id)}
                    className="h-8 w-8 mt-6"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>

            <Button type="button" variant="outline" onClick={addPair} className="w-full">
              <Plus className="h-4 w-4 mr-2" />
              Add Parameter
            </Button>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
