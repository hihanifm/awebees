"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { StatusBar } from "@/components/StatusBar";
import { FilteredResults } from "@/components/playground/FilteredResults";
import { AIResponsePanel } from "@/components/playground/AIResponsePanel";
import { PromptManager } from "@/components/playground/PromptManager";
import { apiClient, getAIConfig } from "@/lib/api-client";
import { loadAISettings } from "@/lib/settings-storage";
import { FilterResult, AISystemPrompts } from "@/lib/api-types";
import { Play, Sparkles, ArrowLeft, Settings, AlertCircle, Search, FileText, X } from "lucide-react";
import Link from "next/link";
import { SettingsDialog } from "@/components/settings/SettingsDialog";

const STORAGE_KEYS = {
  FILE_PATH: "lens_playground_file_path",
  PATTERN: "lens_playground_pattern",
  CUSTOM_FLAGS: "lens_playground_custom_flags",
  CASE_SENSITIVE: "lens_playground_case_sensitive",
  CONTEXT_BEFORE: "lens_playground_context_before",
  CONTEXT_AFTER: "lens_playground_context_after",
  TEXT_INPUT: "lens_playground_text_input",
  SYSTEM_PROMPT: "lens_playground_system_prompt",
  USER_PROMPT: "lens_playground_user_prompt",
  ACTIVE_TAB: "lens_playground_active_tab",
};

export default function PlaygroundPage() {
  const [activeTab, setActiveTab] = useState<"filter" | "text">("filter");

  // Filter mode state
  const [filePath, setFilePath] = useState("");
  const [pattern, setPattern] = useState("");
  const [customFlags, setCustomFlags] = useState("");
  const [caseInsensitive, setCaseInsensitive] = useState(true);
  const [contextBefore, setContextBefore] = useState(0);
  const [contextAfter, setContextAfter] = useState(0);
  const [filterResult, setFilterResult] = useState<FilterResult | null>(null);
  const [filtering, setFiltering] = useState(false);
  const [filterError, setFilterError] = useState<string | null>(null);

  // Text input mode state
  const [textInput, setTextInput] = useState("");

  // Shared AI state
  const [systemPrompt, setSystemPrompt] = useState("");
  const [userPrompt, setUserPrompt] = useState("Please analyze the filtered results above.");
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
    // Check URL query parameter first, then localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get("tab");
    let currentTab: "filter" | "text" = "filter";
    
    if (tabParam === "filter" || tabParam === "text") {
      currentTab = tabParam;
      setActiveTab(tabParam);
    } else {
      // Load active tab from localStorage
      const savedTab = localStorage.getItem(STORAGE_KEYS.ACTIVE_TAB);
      if (savedTab === "filter" || savedTab === "text") {
        currentTab = savedTab;
        setActiveTab(savedTab);
      }
    }

    // Filter mode state
    setFilePath(localStorage.getItem(STORAGE_KEYS.FILE_PATH) || "");
    setPattern(localStorage.getItem(STORAGE_KEYS.PATTERN) || "");
    setCustomFlags(localStorage.getItem(STORAGE_KEYS.CUSTOM_FLAGS) || "");
    setCaseInsensitive(localStorage.getItem(STORAGE_KEYS.CASE_SENSITIVE) !== "false");
    setContextBefore(parseInt(localStorage.getItem(STORAGE_KEYS.CONTEXT_BEFORE) || "0"));
    setContextAfter(parseInt(localStorage.getItem(STORAGE_KEYS.CONTEXT_AFTER) || "0"));
    
    // Text input mode state
    setTextInput(localStorage.getItem(STORAGE_KEYS.TEXT_INPUT) || "");
    
    // Shared prompts from localStorage
    setSystemPrompt(localStorage.getItem(STORAGE_KEYS.SYSTEM_PROMPT) || "");
    const savedUserPrompt = localStorage.getItem(STORAGE_KEYS.USER_PROMPT);
    if (savedUserPrompt) {
      setUserPrompt(savedUserPrompt);
    } else {
      // Set default based on active tab
      setUserPrompt(currentTab === "text" ? "Please analyze the text above." : "Please analyze the filtered results above.");
    }

    // Load default prompts
    apiClient.getAISystemPrompts().then(setDefaultPrompts).catch(console.error);
  }, []);

  // Save active tab to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_TAB, activeTab);
    // Update user prompt default when switching tabs
    if (!localStorage.getItem(STORAGE_KEYS.USER_PROMPT)) {
      setUserPrompt(activeTab === "text" ? "Please analyze the text above." : "Please analyze the filtered results above.");
    }
  }, [activeTab]);

  // Save to localStorage on change
  useEffect(() => {
    if (filePath) localStorage.setItem(STORAGE_KEYS.FILE_PATH, filePath);
  }, [filePath]);

  useEffect(() => {
    if (pattern) localStorage.setItem(STORAGE_KEYS.PATTERN, pattern);
  }, [pattern]);

  useEffect(() => {
    if (customFlags) localStorage.setItem(STORAGE_KEYS.CUSTOM_FLAGS, customFlags);
  }, [customFlags]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.CASE_SENSITIVE, String(caseInsensitive));
  }, [caseInsensitive]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.CONTEXT_BEFORE, String(contextBefore));
  }, [contextBefore]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.CONTEXT_AFTER, String(contextAfter));
  }, [contextAfter]);

  useEffect(() => {
    if (textInput) {
      localStorage.setItem(STORAGE_KEYS.TEXT_INPUT, textInput);
    }
  }, [textInput]);

  // Save shared prompts to localStorage
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

  const handleFilter = async () => {
    if (!filePath.trim() || !pattern.trim()) {
      setFilterError("Please enter both file path and pattern");
      return;
    }

    setFiltering(true);
    setFilterError(null);
    setFilterResult(null);

    try {
      const result = await apiClient.filterFile({
        file_path: filePath.trim(),
        pattern: pattern.trim(),
        custom_flags: customFlags.trim() || undefined,
        case_insensitive: caseInsensitive,
        context_before: contextBefore,
        context_after: contextAfter,
      });
      setFilterResult(result);
    } catch (err) {
      setFilterError(err instanceof Error ? err.message : "Failed to filter file");
    } finally {
      setFiltering(false);
    }
  };

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

  const handleFilterAIAnalyze = async () => {
    if (!filterResult || filterResult.lines.length === 0) {
      setAiError("No filtered results to analyze. Run a filter first.");
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
      setAiError(null);
      return;
    }

    setAiStreaming(true);
    setAiError(null);
    setConfigError(null);
    setAiResponse("");
    setAiExecutionTime(undefined);

    const startTime = Date.now();

    try {
      const content = filterResult.lines.join("\n");
      const fullPrompt = `${systemPrompt}\n\n${userPrompt}`;

      await apiClient.analyzeWithAI(
        content,
        "custom",
        fullPrompt,
        {},
        (chunk) => {
          setAiResponse((prev) => prev + chunk);
        }
      );

      const executionTime = (Date.now() - startTime) / 1000;
      setAiExecutionTime(executionTime);
      setAiStreaming(false);
    } catch (err) {
      const executionTime = (Date.now() - startTime) / 1000;
      setAiExecutionTime(executionTime);
      setAiError(err instanceof Error ? err.message : "Failed to analyze with AI");
      setAiStreaming(false);
    }
  };

  const handleTextAIAnalyze = async () => {
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
      setAiError(null);
      return;
    }

    setAiStreaming(true);
    setAiError(null);
    setConfigError(null);
    setAiResponse("");
    setAiExecutionTime(undefined);

    const startTime = Date.now();

    try {
      const fullPrompt = `${systemPrompt}\n\n${userPrompt}`;

      await apiClient.analyzeWithAI(
        textInput.trim(),
        "custom",
        fullPrompt,
        {},
        (chunk) => {
          setAiResponse((prev) => prev + chunk);
        }
      );

      const executionTime = (Date.now() - startTime) / 1000;
      setAiExecutionTime(executionTime);
      setAiStreaming(false);
    } catch (err) {
      const executionTime = (Date.now() - startTime) / 1000;
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
          <Link 
            href="/"
            className="inline-flex items-center text-sm text-primary hover:text-primary/80 mb-2"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Analysis
          </Link>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
            Playground
          </h1>
          <p className="text-foreground/80 mt-2 font-medium">
            Experiment with filters and AI prompts, or analyze text directly
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "filter" | "text")} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="filter" className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              Filter Mode
            </TabsTrigger>
            <TabsTrigger value="text" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Quick Text
            </TabsTrigger>
          </TabsList>

          {/* Filter Mode Content */}
          <TabsContent value="filter" className="space-y-6 mt-6">
            {/* Step 1: File Input */}
            <section className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground">
                1. Select File
              </h2>
              <div>
                <Label htmlFor="file-path">File Path</Label>
                <Input
                  id="file-path"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                  placeholder="/path/to/your/log/file.txt"
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Enter the absolute path to a file on the server
                </p>
              </div>
            </section>

            {/* Step 2: Ripgrep Filter */}
            <section className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground">
                2. Configure Ripgrep Filter
              </h2>
              <div>
                <Label htmlFor="pattern">Pattern (Regex)</Label>
                <Input
                  id="pattern"
                  value={pattern}
                  onChange={(e) => setPattern(e.target.value)}
                  placeholder="ERROR|FATAL|Exception"
                  className="font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Enter a ripgrep-compatible regex pattern
                </p>
              </div>

              {/* Custom Flags */}
              <div>
                <Label htmlFor="custom-flags">Custom Flags (Optional)</Label>
                <Input
                  id="custom-flags"
                  value={customFlags}
                  onChange={(e) => setCustomFlags(e.target.value)}
                  placeholder="--multiline --pcre2 --max-count 500"
                  className="font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Advanced: Add custom ripgrep flags (e.g., <code className="bg-muted px-1 rounded">--multiline</code>, <code className="bg-muted px-1 rounded">--pcre2</code>)
                </p>
              </div>

              {/* Filter options */}
              <div className="grid grid-cols-3 gap-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="case-insensitive"
                    checked={caseInsensitive}
                    onChange={(e) => setCaseInsensitive(e.target.checked)}
                    className="rounded"
                  />
                  <Label htmlFor="case-insensitive" className="text-sm cursor-pointer">
                    Case insensitive
                  </Label>
                </div>
                <div>
                  <Label htmlFor="context-before" className="text-sm">
                    Lines before
                  </Label>
                  <Input
                    id="context-before"
                    type="number"
                    min="0"
                    max="10"
                    value={contextBefore}
                    onChange={(e) => setContextBefore(parseInt(e.target.value) || 0)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="context-after" className="text-sm">
                    Lines after
                  </Label>
                  <Input
                    id="context-after"
                    type="number"
                    min="0"
                    max="10"
                    value={contextAfter}
                    onChange={(e) => setContextAfter(parseInt(e.target.value) || 0)}
                    className="mt-1"
                  />
                </div>
              </div>

              <Button
                onClick={handleFilter}
                disabled={filtering || !filePath.trim() || !pattern.trim()}
                className="w-full bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90"
              >
                <Play className="h-4 w-4 mr-2" />
                {filtering ? "Filtering..." : "Run Filter"}
              </Button>

              {filterError && (
                <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
                  <p className="text-sm text-red-600 dark:text-red-400">Error: {filterError}</p>
                </div>
              )}
            </section>

            {/* Step 3: Filtered Results */}
            <section className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground">
                3. Filtered Results
              </h2>
              <FilteredResults result={filterResult} loading={filtering} />
            </section>

            {/* Step 4: AI Prompts */}
            {filterResult && filterResult.lines.length > 0 && (
              <section className="space-y-4">
                <h2 className="text-xl font-semibold text-foreground">
                  4. Configure AI Prompts
                </h2>
                <PromptManager
                  systemPrompt={systemPrompt}
                  userPrompt={userPrompt}
                  onSystemPromptChange={setSystemPrompt}
                  onUserPromptChange={setUserPrompt}
                  defaultPrompts={defaultPrompts}
                />
                <Button
                  onClick={handleFilterAIAnalyze}
                  disabled={aiStreaming || !systemPrompt.trim() || !userPrompt.trim()}
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
            )}

            {/* Step 5: AI Response */}
            {(aiResponse || aiStreaming || aiError) && (
              <section className="space-y-4">
                <h2 className="text-xl font-semibold text-foreground">
                  5. AI Analysis
                </h2>
                <AIResponsePanel
                  response={aiResponse}
                  streaming={aiStreaming}
                  error={aiError}
                  executionTime={aiExecutionTime}
                />
              </section>
            )}
          </TabsContent>

          {/* Quick Text Mode Content */}
          <TabsContent value="text" className="space-y-6 mt-6">
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
                onClick={handleTextAIAnalyze}
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
          </TabsContent>
        </Tabs>
      </main>

      <StatusBar onOpenSettings={() => setSettingsOpen(true)} />
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}
