"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { InputWithHistory } from "@/components/ui/input-with-history";
import { TextareaWithHistory } from "@/components/ui/textarea-with-history";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { StatusBar } from "@/components/StatusBar";
import { ResultsPanel } from "@/components/results-panel/ResultsPanel";
import { ProgressWidget } from "@/components/progress/ProgressWidget";
import { ErrorBanner } from "@/components/ErrorBanner";
import { AIResponsePanel } from "@/components/playground/AIResponsePanel";
import { PromptManager } from "@/components/playground/PromptManager";
import { apiClient, getAIConfig } from "@/lib/api-client";
import { loadAISettings } from "@/lib/settings-storage";
import { AnalysisResponse, ProgressEvent, AISystemPrompts } from "@/lib/api-types";
import { Play, Sparkles, Search, FileText, X, AlertCircle } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { logger } from "@/lib/logger";

const STORAGE_KEYS = {
  FILE_PATH: "lens_playground_file_path",
  RIPGREP_COMMAND: "lens_playground_ripgrep_command",
  TEXT_INPUT: "lens_playground_text_input",
  SYSTEM_PROMPT: "lens_playground_system_prompt",
  USER_PROMPT: "lens_playground_user_prompt",
  ACTIVE_TAB: "lens_playground_active_tab",
  FILE_PATH_HISTORY: "lens_playground_file_path_history",
  RIPGREP_COMMAND_HISTORY: "lens_playground_ripgrep_command_history",
};

export default function PlaygroundPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<"filter" | "text">("filter");

  // Filter mode state - using same pattern as main page
  const [filePaths, setFilePaths] = useState<string>("");
  const [ripgrepCommand, setRipgrepCommand] = useState<string>("");
  const [analysisResponse, setAnalysisResponse] = useState<AnalysisResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  // Text input mode state
  const [textInput, setTextInput] = useState("");

  // Shared AI state for text mode
  const [systemPrompt, setSystemPrompt] = useState("");
  const [userPrompt, setUserPrompt] = useState("Please analyze the text above.");
  const [aiResponse, setAiResponse] = useState("");
  const [aiStreaming, setAiStreaming] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiExecutionTime, setAiExecutionTime] = useState<number | undefined>(undefined);
  const [configError, setConfigError] = useState<string | null>(null);

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
    setFilePaths(localStorage.getItem(STORAGE_KEYS.FILE_PATH) || "");
    setRipgrepCommand(localStorage.getItem(STORAGE_KEYS.RIPGREP_COMMAND) || "");
    
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
    if (filePaths) localStorage.setItem(STORAGE_KEYS.FILE_PATH, filePaths);
  }, [filePaths]);

  useEffect(() => {
    if (ripgrepCommand) localStorage.setItem(STORAGE_KEYS.RIPGREP_COMMAND, ripgrepCommand);
  }, [ripgrepCommand]);

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

  // Strip surrounding quotes from a string if they match at both ends
  function stripQuotes(path: string): string {
    if (!path || path.length < 2) {
      return path;
    }

    const first = path[0];
    const last = path[path.length - 1];

    if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
      return path.slice(1, -1);
    }

    return path;
  }

  const handleExecute = async () => {
    if (!filePaths.trim() || !ripgrepCommand.trim()) {
      setError(t("errors.filePathRequired"));
      return;
    }

    // Parse file paths (support multiple paths separated by newlines)
    const paths = filePaths
      .split("\n")
      .map((p) => stripQuotes(p.trim()))
      .filter((p) => p.length > 0);

    if (paths.length === 0) {
      setError(t("errors.filePathRequired"));
      return;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysisResponse(null);
    setProgressEvents([]);
    setCurrentTaskId(null);

    try {
      // Extract task ID from first progress event
      let taskIdExtracted = false;

      // Execute playground with progress tracking
      const response = await apiClient.executePlayground(
        paths,
        ripgrepCommand.trim(),
        (event: ProgressEvent) => {
          setProgressEvents((prev) => [...prev, event]);
          if (!taskIdExtracted && event.task_id) {
            setCurrentTaskId(event.task_id);
            taskIdExtracted = true;
          }
        }
      );

      // Set final response
      setAnalysisResponse(response);
    } catch (err) {
      if (err instanceof Error && err.message === "Analysis cancelled") {
        setError(t("errors.analysisCancelled"));
      } else {
        setError(err instanceof Error ? err.message : t("errors.analysisFailed"));
      }
    } finally {
      setAnalyzing(false);
      setCurrentTaskId(null);
    }
  };

  const handleCancel = async () => {
    if (currentTaskId) {
      try {
        await apiClient.cancelPlayground(currentTaskId);
        setAnalyzing(false);
        setCurrentTaskId(null);
      } catch (err) {
        logger.error("Failed to cancel playground:", err);
      }
    }
  };

  const checkAIConfiguration = async (): Promise<{ isValid: boolean; message?: string }> => {
    try {
      const localSettings = loadAISettings();
      
      if (localSettings && localSettings.apiKey && localSettings.apiKey.trim() !== "") {
        const enabled = localSettings.enabled;
        const baseUrl = localSettings.baseUrl;
        
        if (!enabled) {
          return {
            isValid: false,
            message: "AI processing is not enabled. Please enable it in settings."
          };
        }
        
        if (!baseUrl || baseUrl.trim() === "") {
          return {
            isValid: false,
            message: "AI Base URL is not configured. Please set it in settings."
          };
        }
        
        return { isValid: true };
      }
      
      const backendConfig = await getAIConfig();
      
      if (backendConfig.is_configured) {
        return { isValid: true };
      }
      
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

  const handleTextAIAnalyze = async () => {
    if (!textInput.trim()) {
      setAiError(t("playground.enterText"));
      return;
    }

    if (!systemPrompt.trim() || !userPrompt.trim()) {
      setAiError(t("playground.enterPrompts"));
      return;
    }

    // Check AI configuration before proceeding
    const configCheck = await checkAIConfiguration();
    if (!configCheck.isValid) {
      setConfigError(configCheck.message || t("playground.aiNotConfigured"));
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
      setAiError(err instanceof Error ? err.message : t("aiResponse.failedToAnalyze"));
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
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
            {t("playground.title")}
          </h1>
          <p className="text-foreground/80 mt-2 font-medium">
            {t("playground.description")}
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "filter" | "text")} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="filter" className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              {t("playground.filterMode")}
            </TabsTrigger>
            <TabsTrigger value="text" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {t("playground.quickText")}
            </TabsTrigger>
          </TabsList>

          {/* Filter Mode Content */}
          <TabsContent value="filter" className="space-y-6 mt-6">
            {/* File Paths Input */}
            <section className="space-y-4">
              <h2 className="text-sm font-semibold text-foreground">
                1. {t("app.enterFilePaths")}
              </h2>
              <div>
                <Label htmlFor="file-paths">{t("app.enterFilePaths")}</Label>
                <TextareaWithHistory
                  value={filePaths}
                  onChange={setFilePaths}
                  storageKey={STORAGE_KEYS.FILE_PATH_HISTORY}
                  placeholder={t("app.filePathsPlaceholder")}
                  className="w-full h-[3.5rem] rounded-md border border-input bg-muted px-4 py-2 font-mono text-sm resize-y"
                  rows={2}
                  disabled={analyzing}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {t("app.filePathsHint")}
                </p>
              </div>
            </section>

            {/* Ripgrep Command Input */}
            <section className="space-y-4">
              <h2 className="text-sm font-semibold text-foreground">
                2. Ripgrep Command
              </h2>
              <div>
                <Label htmlFor="ripgrep-command">Ripgrep Command</Label>
                <InputWithHistory
                  id="ripgrep-command"
                  value={ripgrepCommand}
                  onChange={setRipgrepCommand}
                  storageKey={STORAGE_KEYS.RIPGREP_COMMAND_HISTORY}
                  placeholder='e.g., ERROR or -i -A 2 ERROR'
                  className="font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Enter the complete ripgrep command (everything after 'rg'). Examples: "ERROR", "-i ERROR", "-A 2 ERROR". See <a href="/docs/RIPGREP_GUIDE.md" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline font-medium">Ripgrep Guide</a> for more details.
                </p>
              </div>

              <Button
                onClick={handleExecute}
                disabled={analyzing || !filePaths.trim() || !ripgrepCommand.trim()}
                className="w-full bg-gradient-to-r from-primary to-accent hover:from-primary/90 hover:to-accent/90 font-bold"
              >
                <Play className="h-4 w-4 mr-2" />
                {analyzing ? t("app.analyzing") : "Execute"}
              </Button>

              {error && (
                <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
                  <p className="text-sm text-red-600 dark:text-red-400">Error: {error}</p>
                </div>
              )}
            </section>

            {/* Progress Widget */}
            {progressEvents.length > 0 && (
              <section>
                <ProgressWidget
                  events={progressEvents}
                  currentTaskId={currentTaskId}
                  onCancel={handleCancel}
                />
              </section>
            )}

            {/* Results Panel */}
            {analysisResponse && (
              <section>
                <ResultsPanel analysisResponse={analysisResponse} loading={analyzing} />
              </section>
            )}
          </TabsContent>

          {/* Quick Text Mode Content */}
          <TabsContent value="text" className="space-y-6 mt-6">
            {/* Step 1: Text Input */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-foreground">
                  1. {t("playground.pasteText")}
                </h2>
                {textInput && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearText}
                    className="text-muted-foreground hover:text-foreground font-bold"
                  >
                    <X className="h-4 w-4 mr-1" />
                    {t("common.clear")}
                  </Button>
                )}
              </div>
              <div>
                <Label htmlFor="text-input">{t("playground.textContent")}</Label>
                <Textarea
                  id="text-input"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder={t("playground.textPlaceholder")}
                  className="font-mono text-sm min-h-64 resize-y"
                />
                <div className="flex items-center justify-between mt-1">
                  <p className="text-xs text-muted-foreground">
                    {t("playground.textHint")}
                  </p>
                  {textInput && (
                    <p className="text-xs text-muted-foreground">
                      {textLines} {textLines !== 1 ? t("playground.linesPlural") : t("playground.lines")} • {textChars.toLocaleString()} {textChars !== 1 ? t("playground.charactersPlural") : t("playground.characters")}
                    </p>
                  )}
                </div>
              </div>
            </section>

            {/* Step 2: AI Prompts */}
            <section className="space-y-4">
              <h2 className="text-sm font-semibold text-foreground">
                2. {t("playground.configureAIPrompts")}
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
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:shadow-md font-bold justify-center"
              >
                <Sparkles className="h-4 w-4 mr-2 text-white" />
                {aiStreaming ? t("playground.analyzingWithAI") : t("playground.analyzeWithAI")}
              </Button>
              {configError && (
                <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-950/30">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                        {t("playground.aiConfigRequired")}
                      </p>
                      <p className="text-sm text-amber-800 dark:text-amber-200">
                        {configError}
                      </p>
                      <div className="text-xs text-amber-700 dark:text-amber-300 space-y-1">
                        <p>{t("playground.aiConfigMessage")}</p>
                        <ul className="list-disc list-inside space-y-0.5 ml-2">
                          <li>{t("playground.enableAI")}</li>
                          <li>{t("playground.setBaseURL")}</li>
                          <li>{t("playground.provideAPIKey")}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </section>

            {/* Step 3: AI Response */}
            {(aiResponse || aiStreaming || aiError) && (
              <section className="space-y-4">
                <h2 className="text-sm font-semibold text-foreground">
                  3. {t("playground.aiAnalysis")}
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

      <StatusBar />
    </div>
  );
}
