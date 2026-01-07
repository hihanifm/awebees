"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { StatusBar } from "@/components/StatusBar";
import { AIResponsePanel } from "@/components/playground/AIResponsePanel";
import { PromptManager } from "@/components/playground/PromptManager";
import { apiClient, getAIConfig } from "@/lib/api-client";
import { loadAISettings } from "@/lib/settings-storage";
import { AISystemPrompts } from "@/lib/api-types";
import { Sparkles, ArrowLeft, Settings, AlertCircle, X } from "lucide-react";
import Link from "next/link";
import { SettingsDialog } from "@/components/settings/SettingsDialog";

const STORAGE_KEYS = {
  TEXT_INPUT: "lens_playground_text_input",
  SYSTEM_PROMPT: "lens_playground_system_prompt",
  USER_PROMPT: "lens_playground_user_prompt",
};

export default function TextInputPage() {
  const [textInput, setTextInput] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [userPrompt, setUserPrompt] = useState("Please analyze the text above.");
  const [aiResponse, setAiResponse] = useState("");
  const [aiStreaming, setAiStreaming] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiExecutionTime, setAiExecutionTime] = useState<number | undefined>(undefined);
  const [configError, setConfigError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const [defaultPrompts, setDefaultPrompts] = useState<AISystemPrompts>({
    summarize: "",
    explain: "",
    recommend: "",
  });

  // Load saved values from localStorage on mount
  useEffect(() => {
    setTextInput(localStorage.getItem(STORAGE_KEYS.TEXT_INPUT) || "");
    setSystemPrompt(localStorage.getItem(STORAGE_KEYS.SYSTEM_PROMPT) || "");
    setUserPrompt(localStorage.getItem(STORAGE_KEYS.USER_PROMPT) || "Please analyze the text above.");

    // Load default prompts
    apiClient.getAISystemPrompts().then(setDefaultPrompts).catch(console.error);
  }, []);

  // Save to localStorage on change
  useEffect(() => {
    if (textInput) {
      localStorage.setItem(STORAGE_KEYS.TEXT_INPUT, textInput);
    }
  }, [textInput]);

  useEffect(() => {
    if (systemPrompt) {
      localStorage.setItem(STORAGE_KEYS.SYSTEM_PROMPT, systemPrompt);
    }
  }, [systemPrompt]);

  useEffect(() => {
    if (userPrompt) {
      localStorage.setItem(STORAGE_KEYS.USER_PROMPT, userPrompt);
    }
  }, [userPrompt]);

  const checkAIConfiguration = async (): Promise<{ isValid: boolean; message?: string }> => {
    try {
      // Frontend localStorage is the source of truth once user saves valid settings
      const localSettings = loadAISettings();
      
      // Check if localStorage has valid settings (user has explicitly configured)
      if (localSettings && localSettings.apiKey && localSettings.apiKey.trim() !== "") {
        // User has saved settings - localStorage is source of truth
        const enabled = localSettings.enabled;
        const baseUrl = localSettings.baseUrl;
        const apiKey = localSettings.apiKey;
        
        // Check if AI is enabled
        if (!enabled) {
          return {
            isValid: false,
            message: "AI processing is not enabled. Please enable it in settings."
          };
        }
        
        // Check if base URL is configured
        if (!baseUrl || baseUrl.trim() === "") {
          return {
            isValid: false,
            message: "AI Base URL is not configured. Please set it in settings."
          };
        }
        
        return { isValid: true };
      }
      
      // No valid localStorage settings - check backend config (initial load or backend .env)
      const backendConfig = await getAIConfig();
      
      // If backend says it's configured, trust it (backend uses .env file)
      if (backendConfig.is_configured) {
        return { isValid: true };
      }
      
      // Backend is not configured either
      return {
        isValid: false,
        message: "AI is not configured. Please configure it in settings."
      };
    } catch (error) {
      return {
        isValid: false,
        message: "Failed to check AI configuration. Please verify your settings."
      };
    }
  };

  const handleAIAnalyze = async () => {
    if (!textInput.trim()) {
      setAiError("Please enter some text to analyze.");
      return;
    }

    if (!systemPrompt.trim() || !userPrompt.trim()) {
      setAiError("Please enter both system and user prompts");
      return;
    }

    // Check AI configuration before proceeding
    const configCheck = await checkAIConfiguration();
    if (!configCheck.isValid) {
      setConfigError(configCheck.message || "AI is not properly configured. Please configure AI settings.");
      setAiError(null); // Clear any previous errors
      return;
    }

    setAiStreaming(true);
    setAiError(null);
    setConfigError(null); // Clear config error if we got past the check
    setAiResponse("");
    setAiExecutionTime(undefined);

    const startTime = Date.now();

    try {
      // Build full prompt with context
      const fullPrompt = `${systemPrompt}\n\n${userPrompt}`;

      // Stream AI response using callback
      await apiClient.analyzeWithAI(
        textInput.trim(),
        "custom",
        fullPrompt,
        {},
        (chunk) => {
          // Update response as chunks arrive
          setAiResponse((prev) => prev + chunk);
        }
      );

      // Analysis complete - calculate execution time
      const executionTime = (Date.now() - startTime) / 1000; // Convert to seconds
      setAiExecutionTime(executionTime);
      setAiStreaming(false);
    } catch (err) {
      const executionTime = (Date.now() - startTime) / 1000; // Track time even on error
      setAiExecutionTime(executionTime);
      setAiError(err instanceof Error ? err.message : "Failed to analyze with AI");
      setAiStreaming(false);
    }
  };

  const handleClearText = () => {
    setTextInput("");
    localStorage.removeItem(STORAGE_KEYS.TEXT_INPUT);
  };

  const textLines = textInput.split("\n").length;
  const textChars = textInput.length;

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5 font-sans">
      <main className="flex min-h-screen w-full max-w-[90%] flex-col gap-6 pb-8 px-4 mx-auto bg-background/80 backdrop-blur-sm border-x border-border">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary/10 via-accent/5 to-primary/10 -mx-4 px-6 py-4">
          <div className="flex items-center justify-between mb-2">
            <Link 
              href="/"
              className="inline-flex items-center text-sm text-primary hover:text-primary/80"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Analysis
            </Link>
            <Link 
              href="/playground"
              className="inline-flex items-center text-sm text-primary hover:text-primary/80"
            >
              Filter Mode
            </Link>
          </div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
            Playground - Text Input
          </h1>
          <p className="text-foreground/80 mt-2 font-medium">
            Paste text directly and analyze it with AI
          </p>
        </div>

        <div className="space-y-6">
          {/* Step 1: Text Input */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-foreground">
                1. Paste Text
              </h2>
              {textInput && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearText}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              )}
            </div>
            <div>
              <Label htmlFor="text-input">Text Content</Label>
              <Textarea
                id="text-input"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Paste or type your text here..."
                className="font-mono text-sm min-h-64 resize-y"
              />
              <div className="flex items-center justify-between mt-1">
                <p className="text-xs text-muted-foreground">
                  Enter or paste the text you want to analyze
                </p>
                {textInput && (
                  <p className="text-xs text-muted-foreground">
                    {textLines} line{textLines !== 1 ? "s" : ""} • {textChars.toLocaleString()} character{textChars !== 1 ? "s" : ""}
                  </p>
                )}
              </div>
            </div>
          </section>

          {/* Step 2: AI Prompts */}
          <section className="space-y-4">
            <h2 className="text-xl font-semibold text-foreground">
              2. Configure AI Prompts
            </h2>
            <PromptManager
              systemPrompt={systemPrompt}
              userPrompt={userPrompt}
              onSystemPromptChange={setSystemPrompt}
              onUserPromptChange={setUserPrompt}
              defaultPrompts={defaultPrompts}
            />
            <Button
              onClick={handleAIAnalyze}
              disabled={aiStreaming || !textInput.trim() || !systemPrompt.trim() || !userPrompt.trim()}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {aiStreaming ? "Analyzing..." : "Analyze with AI"}
            </Button>
              {configError && (
                <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-950/30">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                        AI Configuration Required
                      </p>
                      <p className="text-sm text-amber-800 dark:text-amber-200">
                        {configError}
                      </p>
                      <div className="text-xs text-amber-700 dark:text-amber-300 space-y-1">
                        <p>To use AI analysis, please configure:</p>
                        <ul className="list-disc list-inside space-y-0.5 ml-2">
                          <li>Enable AI processing</li>
                          <li>Set the AI Base URL (e.g., https://api.openai.com/v1)</li>
                          <li>Provide your API Key</li>
                        </ul>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSettingsOpen(true)}
                        className="mt-2 border-amber-300 text-amber-900 hover:bg-amber-100 dark:border-amber-700 dark:text-amber-100 dark:hover:bg-amber-900/50"
                      >
                        <Settings className="mr-2 h-4 w-4" />
                        Open Settings
                      </Button>
                    </div>
                  </div>
                </div>
              )}
          </section>

          {/* Step 3: AI Response */}
          {(aiResponse || aiStreaming || aiError) && (
            <section className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground">
                3. AI Analysis
              </h2>
              <AIResponsePanel
                response={aiResponse}
                streaming={aiStreaming}
                error={aiError}
                executionTime={aiExecutionTime}
              />
            </section>
          )}
        </div>
      </main>

      <StatusBar onOpenSettings={() => setSettingsOpen(true)} />
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}

