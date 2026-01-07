"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Save, Trash2, Plus } from "lucide-react";
import { SavedPrompt, AISystemPrompts } from "@/lib/api-types";
import { useToast } from "@/components/ui/use-toast";

const STORAGE_KEY = "lens_playground_prompts";

interface PromptManagerProps {
  systemPrompt: string;
  userPrompt: string;
  onSystemPromptChange: (prompt: string) => void;
  onUserPromptChange: (prompt: string) => void;
  defaultPrompts: AISystemPrompts;
}

export function PromptManager({
  systemPrompt,
  userPrompt,
  onSystemPromptChange,
  onUserPromptChange,
  defaultPrompts,
}: PromptManagerProps) {
  const { toast } = useToast();
  const [savedPrompts, setSavedPrompts] = useState<SavedPrompt[]>([]);
  const [selectedPromptId, setSelectedPromptId] = useState<string>("none");
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [newPromptName, setNewPromptName] = useState("");

  // Load saved prompts from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setSavedPrompts(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to parse saved prompts:", e);
      }
    }
  }, []);

  // Save prompts to localStorage
  const saveToStorage = (prompts: SavedPrompt[]) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prompts));
    setSavedPrompts(prompts);
  };

  const handlePresetSelect = (value: string) => {
    setSelectedPromptId(value);
    
    if (value === "none") {
      return;
    }

    if (value === "summarize" || value === "explain" || value === "recommend") {
      onSystemPromptChange(defaultPrompts[value]);
      onUserPromptChange("Please analyze the filtered results above.");
      toast({
        title: "Preset loaded",
        description: `Loaded "${value}" preset prompt`,
      });
    } else {
      // Load custom saved prompt
      const prompt = savedPrompts.find((p) => p.id === value);
      if (prompt) {
        onSystemPromptChange(prompt.systemPrompt);
        onUserPromptChange(prompt.userPrompt);
        toast({
          title: "Prompt loaded",
          description: `Loaded "${prompt.name}"`,
        });
      }
    }
  };

  const handleSavePrompt = () => {
    if (!newPromptName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a name for the prompt",
        variant: "destructive",
      });
      return;
    }

    const newPrompt: SavedPrompt = {
      id: Date.now().toString(),
      name: newPromptName.trim(),
      systemPrompt,
      userPrompt,
      createdAt: new Date().toISOString(),
    };

    const updated = [...savedPrompts, newPrompt];
    saveToStorage(updated);
    setNewPromptName("");
    setSaveDialogOpen(false);
    setSelectedPromptId(newPrompt.id);

    toast({
      title: "Prompt saved",
      description: `Saved as "${newPrompt.name}"`,
    });
  };

  const handleDeletePrompt = (id: string) => {
    const updated = savedPrompts.filter((p) => p.id !== id);
    saveToStorage(updated);
    if (selectedPromptId === id) {
      setSelectedPromptId("none");
    }
    toast({
      title: "Prompt deleted",
      description: "Custom prompt removed",
    });
  };

  return (
    <div className="space-y-4">
      {/* Preset selector */}
      <div className="flex items-end gap-2">
        <div className="flex-1">
          <Label htmlFor="preset-select">Load Preset or Saved Prompt</Label>
          <Select value={selectedPromptId} onValueChange={handlePresetSelect}>
            <SelectTrigger id="preset-select">
              <SelectValue placeholder="Select a preset..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None (Custom)</SelectItem>
              <SelectItem value="summarize">Summarize</SelectItem>
              <SelectItem value="explain">Explain</SelectItem>
              <SelectItem value="recommend">Recommend</SelectItem>
              {savedPrompts.length > 0 && (
                <>
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                    Custom Saved Prompts
                  </div>
                  {savedPrompts.map((prompt) => (
                    <div key={prompt.id} className="flex items-center justify-between px-2 hover:bg-accent">
                      <SelectItem value={prompt.id} className="flex-1">
                        {prompt.name}
                      </SelectItem>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleDeletePrompt(prompt.id);
                        }}
                        className="h-6 w-6 p-0 hover:bg-red-100 dark:hover:bg-red-900/30"
                      >
                        <Trash2 className="h-3 w-3 text-red-600 dark:text-red-400" />
                      </Button>
                    </div>
                  ))}
                </>
              )}
            </SelectContent>
          </Select>
        </div>
        {!saveDialogOpen ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSaveDialogOpen(true)}
            className="border-orange-300 text-orange-700 hover:bg-orange-50 dark:border-orange-800 dark:text-orange-300 dark:hover:bg-orange-900/30"
          >
            <Save className="h-4 w-4 mr-2" />
            Save Current
          </Button>
        ) : (
          <div className="flex gap-2">
            <Input
              placeholder="Prompt name..."
              value={newPromptName}
              onChange={(e) => setNewPromptName(e.target.value)}
              className="w-40"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSavePrompt();
                if (e.key === "Escape") setSaveDialogOpen(false);
              }}
            />
            <Button size="sm" onClick={handleSavePrompt}>
              <Plus className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSaveDialogOpen(false);
                setNewPromptName("");
              }}
            >
              Cancel
            </Button>
          </div>
        )}
      </div>

      {/* System prompt */}
      <div>
        <Label htmlFor="system-prompt">System Prompt</Label>
        <Textarea
          id="system-prompt"
          value={systemPrompt}
          onChange={(e) => onSystemPromptChange(e.target.value)}
          placeholder="Enter the system prompt that defines the AI's role..."
          className="font-mono text-sm min-h-32 resize-y"
        />
        <p className="text-xs text-muted-foreground mt-1">
          Defines how the AI should behave and what perspective it should take.
        </p>
      </div>

      {/* User prompt */}
      <div>
        <Label htmlFor="user-prompt">User Prompt</Label>
        <Textarea
          id="user-prompt"
          value={userPrompt}
          onChange={(e) => onUserPromptChange(e.target.value)}
          placeholder="Enter your analysis request..."
          className="font-mono text-sm min-h-24 resize-y"
        />
        <p className="text-xs text-muted-foreground mt-1">
          The specific analysis or question you want answered about the filtered results.
        </p>
      </div>
    </div>
  );
}

