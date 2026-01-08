"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AnalysisResponse } from "@/lib/api-types";
import { analyzeWithAI, getAIConfig } from "@/lib/api-client";
import { loadAISettings } from "@/lib/settings-storage";
import { Sparkles, Copy, RefreshCw, ChevronDown, ChevronUp, Loader2, Settings, AlertCircle, Check } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useTranslation } from "@/lib/i18n";

interface ResultsPanelProps {
  analysisResponse: AnalysisResponse;
  loading?: boolean;
  onOpenSettings?: () => void;
}

interface AIAnalysisState {
  status: "idle" | "loading" | "streaming" | "complete" | "error";
  response: string;
  error?: string;
  executionTime?: number; // Time taken in seconds
}

export function ResultsPanel({ analysisResponse, loading, onOpenSettings }: ResultsPanelProps) {
  const { t } = useTranslation();
  const [aiStates, setAiStates] = useState<Record<string, AIAnalysisState>>({});
  const [promptTypes, setPromptTypes] = useState<Record<string, string>>({});
  const [customPrompts, setCustomPrompts] = useState<Record<string, string>>({});
  const [showAI, setShowAI] = useState<Record<string, boolean>>({});
  const [showCustomPrompt, setShowCustomPrompt] = useState<Record<string, boolean>>({});
  const [configErrors, setConfigErrors] = useState<Record<string, string>>({});
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});

  if (loading) {
    return (
      <div className="text-center py-8 text-muted-foreground">{t("app.analyzing")}</div>
    );
  }

  const { results, total_time, insights_count } = analysisResponse;

  if (results.length === 0) {
    return null;
  }

  const formatTime = (seconds: number): string => {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
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
            message: t("playground.enableAI") + ". " + t("playground.openSettings")
          };
        }
        
        // Check if base URL is configured
        if (!baseUrl || baseUrl.trim() === "") {
          return {
            isValid: false,
            message: t("playground.setBaseURL") + ". " + t("playground.openSettings")
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
        message: t("playground.aiNotConfigured")
      };
    } catch (error) {
      console.error("[ResultsPanel] Error checking configuration:", error);
      return {
        isValid: false,
        message: "Failed to check AI configuration. Please verify your settings."
      };
    }
  };

  const handleAIAnalyze = async (insightId: string, content: string) => {
    // Clear any previous config errors for this insight
    setConfigErrors(prev => {
      const updated = { ...prev };
      delete updated[insightId];
      return updated;
    });

    // Check AI configuration before proceeding
    const configCheck = await checkAIConfiguration();
    if (!configCheck.isValid) {
      setConfigErrors(prev => ({
        ...prev,
        [insightId]: configCheck.message || "AI is not properly configured."
      }));
      setAiStates(prev => ({
        ...prev,
        [insightId]: {
          status: "error",
          response: "",
          error: configCheck.message || "Configuration error",
        }
      }));
      return;
    }

    const promptType = promptTypes[insightId] || "explain";
    const customPrompt = customPrompts[insightId];

    // Validate custom prompt if needed
    if (promptType === "custom" && (!customPrompt || customPrompt.trim() === "")) {
      setConfigErrors(prev => ({
        ...prev,
        [insightId]: "Please enter a custom prompt."
      }));
      setAiStates(prev => ({
        ...prev,
        [insightId]: {
          status: "error",
          response: "",
          error: "Custom prompt is required.",
        }
      }));
      return;
    }

    // Initialize or update AI state
    const startTime = Date.now();
    setAiStates(prev => ({
      ...prev,
      [insightId]: {
        status: "streaming",
        response: "",
      }
    }));

    try {
      let fullResponse = "";
      await analyzeWithAI(
        content,
        promptType,
        promptType === "custom" ? customPrompt : undefined,
        undefined,
        (chunk) => {
          fullResponse += chunk;
          setAiStates(prev => ({
            ...prev,
            [insightId]: {
              status: "streaming",
              response: fullResponse,
            }
          }));
        }
      );

      const executionTime = (Date.now() - startTime) / 1000; // Convert to seconds
      setAiStates(prev => ({
        ...prev,
        [insightId]: {
          status: "complete",
          response: fullResponse,
          executionTime,
        }
      }));
    } catch (error) {
      const executionTime = (Date.now() - startTime) / 1000; // Track time even on error
      setAiStates(prev => ({
        ...prev,
        [insightId]: {
          status: "error",
          response: "",
          error: String(error),
          executionTime,
        }
      }));
    }
  };

  const handleCopyAI = (response: string) => {
    navigator.clipboard.writeText(response);
  };

  const handleCopyResult = (insightId: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedStates(prev => ({ ...prev, [insightId]: true }));
    setTimeout(() => {
      setCopiedStates(prev => ({ ...prev, [insightId]: false }));
    }, 2000);
  };

  const handleToggleAI = (insightId: string) => {
    setShowAI(prev => ({ ...prev, [insightId]: !prev[insightId] }));
  };

  const handlePromptTypeChange = (insightId: string, value: string) => {
    setPromptTypes(prev => ({ ...prev, [insightId]: value }));
    setShowCustomPrompt(prev => ({ ...prev, [insightId]: value === "custom" }));
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{t("results.analysisResults")}</h2>
      
      {/* Statistics Card */}
      <Card className="bg-gradient-to-br from-orange-50 via-amber-50 to-orange-50 dark:from-orange-950/30 dark:via-amber-950/20 dark:to-orange-950/30 border-2 border-orange-200 dark:border-orange-800/50">
        <CardHeader>
          <CardTitle className="text-base text-orange-900 dark:text-orange-100">{t("results.analysisStatistics")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">{t("results.insightsRun")}</span>
              <span className="text-2xl font-bold text-orange-700 dark:text-orange-300">{insights_count}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">{t("results.totalTime")}</span>
              <span className="text-2xl font-bold text-orange-700 dark:text-orange-300">{formatTime(total_time)}</span>
            </div>
            <div className="flex flex-col sm:col-span-1">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">{t("results.individualTimes")}</span>
              <div className="text-xs space-y-1 mt-1">
                {results.map((resultItem) => (
                  <div key={resultItem.insight_id} className="flex justify-between items-center">
                    <span className="text-orange-800 dark:text-orange-200 truncate mr-2 max-w-[150px]" title={resultItem.insight_id}>
                      {resultItem.insight_id}
                    </span>
                    <span className="font-semibold text-orange-700 dark:text-orange-300">
                      {formatTime(resultItem.execution_time)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        {results.map((resultItem, index) => (
          <Card key={resultItem.insight_id}>
            <CardHeader>
              <CardTitle className="text-base flex justify-between items-center">
                <span>{t("results.insight")}: {resultItem.insight_id}</span>
                <span className="text-xs font-normal text-muted-foreground">
                  {formatTime(resultItem.execution_time)}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {resultItem.result.result_type === "text" && (
                <div className="space-y-4">
                  {/* Header with metadata and copy button */}
                  {resultItem.result.metadata && (
                    <div className="border border-primary/20 rounded-lg overflow-hidden">
                      {/* Header bar */}
                      <div className="bg-gradient-to-r from-primary/10 to-accent/10 px-4 py-3 border-b border-primary/20 flex items-center justify-between">
                        <div className="flex items-center gap-4 text-sm">
                          {resultItem.result.metadata.line_count !== undefined && (
                            <span className="text-foreground font-medium">
                              {resultItem.result.metadata.line_count} {resultItem.result.metadata.line_count === 1 ? t("results.lineFound") : t("results.linesFound")}
                            </span>
                          )}
                          <span className="text-muted-foreground">
                            {formatTime(resultItem.execution_time)}
                          </span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopyResult(resultItem.insight_id, resultItem.result.content)}
                          className="text-primary hover:bg-primary/10"
                        >
                          {copiedStates[resultItem.insight_id] ? (
                            <>
                              <Check className="h-4 w-4 mr-2" />
                              {t("common.copied")}
                            </>
                          ) : (
                            <>
                              <Copy className="h-4 w-4 mr-2" />
                              {t("common.copy")}
                            </>
                          )}
                        </Button>
                      </div>

                      {/* Command display */}
                      {resultItem.result.metadata.execution_command && (
                        <div className="bg-muted px-4 py-2 border-b border-primary/20">
                          <code className="text-xs text-muted-foreground font-mono">
                            $ {resultItem.result.metadata.execution_command}
                          </code>
                        </div>
                      )}

                      {/* Results */}
                      <div className="bg-primary/5 overflow-auto max-h-[600px] border-t border-primary/20">
                        <pre className="p-4 text-sm font-mono text-foreground whitespace-pre-wrap">
                          {resultItem.result.content.split('\n').map((line, index) => (
                            <div key={index} className="flex hover:bg-primary/10">
                              <span className="text-primary select-none mr-4 text-right w-12 flex-shrink-0 font-semibold">
                                {index + 1}
                              </span>
                              <span className="flex-1">{line || ' '}</span>
                            </div>
                          ))}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Fallback: Simple display if no metadata */}
                  {!resultItem.result.metadata && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          {formatTime(resultItem.execution_time)}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopyResult(resultItem.insight_id, resultItem.result.content)}
                          className="text-primary hover:bg-primary/10"
                        >
                          {copiedStates[resultItem.insight_id] ? (
                            <>
                              <Check className="h-4 w-4 mr-2" />
                              {t("common.copied")}
                            </>
                          ) : (
                            <>
                              <Copy className="h-4 w-4 mr-2" />
                              {t("common.copy")}
                            </>
                          )}
                        </Button>
                      </div>
                      <pre className="whitespace-pre-wrap rounded-md border border-border bg-muted p-4 font-mono text-sm overflow-x-auto overflow-y-auto max-h-[600px]">
                        {resultItem.result.content}
                      </pre>
                    </div>
                  )}

                  {/* Auto-triggered AI Analysis Card - Success */}
                  {resultItem.result.ai_analysis && (
                    <Card className="border-blue-500 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Sparkles className="h-4 w-4 text-blue-500" />
                          <span>{t("playground.aiAnalysis")} (Auto)</span>
                          <span className="text-xs text-muted-foreground">
                            ({formatTime(resultItem.execution_time)})
                          </span>
                          <Badge variant="secondary" className="ml-auto text-xs">
                            {resultItem.result.ai_prompt_type || "custom"}
                          </Badge>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap text-sm">
                          {resultItem.result.ai_analysis}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Auto-triggered AI Analysis Card - Error */}
                  {resultItem.result.ai_analysis_error && (
                    <Card className="border-red-500 dark:border-red-800 bg-red-50/50 dark:bg-red-950/20">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 text-red-500" />
                          <span>{t("playground.aiAnalysis")} (Auto) - Error</span>
                          <Badge variant="destructive" className="ml-auto text-xs">
                            Failed
                          </Badge>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <p className="text-sm text-red-900 dark:text-red-100 font-medium">
                            AI analysis failed during automatic execution:
                          </p>
                          <div className="rounded-md bg-red-100 dark:bg-red-900/30 p-3 text-sm text-red-800 dark:text-red-200 font-mono whitespace-pre-wrap">
                            {resultItem.result.ai_analysis_error}
                          </div>
                          <p className="text-xs text-red-700 dark:text-red-300 mt-2">
                            You can still manually analyze this result using the "Analyze with AI" section below with different settings or a shorter prompt.
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* AI Analysis Section */}
                  {resultItem.result.ai_enabled && (
                    <div className="border-t pt-4">
                      <Button
                        onClick={() => handleToggleAI(resultItem.insight_id)}
                        className="mb-2 w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0 shadow-md hover:shadow-lg transition-all duration-200 font-bold relative"
                        size="sm"
                      >
                        <span className="flex items-center gap-2 justify-center">
                          <Sparkles className="h-4 w-4 text-white" />
                          {resultItem.result.ai_analysis ? t("playground.analyzeWithAI") + " (Re-analyze)" : t("playground.analyzeWithAI")}
                        </span>
                        <span className="absolute right-4">
                          {showAI[resultItem.insight_id] ? (
                            <ChevronUp className="h-4 w-4 text-white" />
                          ) : (
                            <ChevronDown className="h-4 w-4 text-white" />
                          )}
                        </span>
                      </Button>

                      {showAI[resultItem.insight_id] && (
                        <div className="space-y-3 mt-3">
                          {/* Configuration Error Alert */}
                          {configErrors[resultItem.insight_id] && (
                            <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-950/30">
                              <div className="flex items-start gap-3">
                                <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1 space-y-2">
                                  <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                                    AI Configuration Required
                                  </p>
                                  <p className="text-sm text-amber-800 dark:text-amber-200">
                                    {configErrors[resultItem.insight_id]}
                                  </p>
                                  <div className="text-xs text-amber-700 dark:text-amber-300 space-y-1">
                                    <p>To use AI analysis, please configure:</p>
                                    <ul className="list-disc list-inside space-y-0.5 ml-2">
                                      <li>Enable AI processing</li>
                                      <li>Set the AI Base URL (e.g., https://api.openai.com/v1)</li>
                                      <li>Provide your API Key</li>
                                    </ul>
                                  </div>
                                  {onOpenSettings && (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={onOpenSettings}
                                      className="mt-2 border-amber-300 text-amber-900 hover:bg-amber-100 dark:border-amber-700 dark:text-amber-100 dark:hover:bg-amber-900/50"
                                    >
                                      <Settings className="mr-2 h-4 w-4" />
                                      Open Settings
                                    </Button>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Prompt Type Selector */}
                          <div className="flex gap-2">
                            <Select
                              value={promptTypes[resultItem.insight_id] || "explain"}
                              onValueChange={(value) => handlePromptTypeChange(resultItem.insight_id, value)}
                            >
                              <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="Select prompt type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="summarize">Summarize</SelectItem>
                                <SelectItem value="explain">Explain</SelectItem>
                                <SelectItem value="recommend">Recommend</SelectItem>
                                <SelectItem value="custom">Custom</SelectItem>
                              </SelectContent>
                            </Select>

                            <Button
                              onClick={() => handleAIAnalyze(resultItem.insight_id, resultItem.result.content)}
                              disabled={aiStates[resultItem.insight_id]?.status === "streaming"}
                              size="sm"
                              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed font-bold justify-center"
                            >
                              {aiStates[resultItem.insight_id]?.status === "streaming" ? (
                                <>
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin text-white" />
                                  Analyzing...
                                </>
                              ) : (
                                <>
                                  <Sparkles className="mr-2 h-4 w-4 text-white" />
                                  Analyze
                                </>
                              )}
                            </Button>
                          </div>

                          {/* Custom Prompt Textarea */}
                          {showCustomPrompt[resultItem.insight_id] && (
                            <Textarea
                              placeholder="Enter your custom prompt..."
                              value={customPrompts[resultItem.insight_id] || ""}
                              onChange={(e) =>
                                setCustomPrompts(prev => ({
                                  ...prev,
                                  [resultItem.insight_id]: e.target.value
                                }))
                              }
                              rows={3}
                              className="text-sm"
                            />
                          )}

                          {/* AI Response */}
                          {aiStates[resultItem.insight_id] && (
                            <div className="rounded-md border border-blue-500 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20 p-4">
                              {aiStates[resultItem.insight_id].status === "error" ? (
                                <div className="text-red-600 text-sm">
                                  Error: {aiStates[resultItem.insight_id].error}
                                </div>
                              ) : aiStates[resultItem.insight_id].response ? (
                                <>
                                  <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs font-semibold text-blue-700 dark:text-blue-300 uppercase">
                                        {t("playground.aiAnalysis")}
                                      </span>
                                      {aiStates[resultItem.insight_id].executionTime !== undefined ? (
                                        <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                                          ({formatTime(aiStates[resultItem.insight_id].executionTime!)})
                                        </span>
                                      ) : aiStates[resultItem.insight_id].status === "streaming" ? (
                                        <span className="text-xs text-blue-500 dark:text-blue-400">
                                          (analyzing...)
                                        </span>
                                      ) : null}
                                    </div>
                                    <div className="flex gap-2">
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleCopyAI(aiStates[resultItem.insight_id].response)}
                                      >
                                        <Copy className="h-3 w-3" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleAIAnalyze(resultItem.insight_id, resultItem.result.content)}
                                      >
                                        <RefreshCw className="h-3 w-3" />
                                      </Button>
                                    </div>
                                  </div>
                                  <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                                    {aiStates[resultItem.insight_id].response}
                                    {aiStates[resultItem.insight_id].status === "streaming" && (
                                      <span className="inline-block w-2 h-4 ml-1 bg-blue-500 animate-pulse" />
                                    )}
                                  </div>
                                </>
                              ) : (
                                <div className="text-sm text-muted-foreground">
                                  Click "Analyze" to get AI insights...
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
              {resultItem.result.result_type === "file" && (
                <div className="text-sm text-muted-foreground">
                  File: {resultItem.result.content}
                </div>
              )}
              {resultItem.result.result_type === "chart_data" && (
                <div className="text-sm text-muted-foreground">
                  Chart data (JSON): <pre className="mt-2 whitespace-pre-wrap rounded-md border border-border bg-muted p-4 font-mono text-xs overflow-x-auto">{resultItem.result.content}</pre>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

