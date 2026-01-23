"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { AnalysisResponse } from "@/lib/api-types";
import { analyzeWithAI, getAIConfig, apiClient } from "@/lib/api-client";
import { loadAISettings, loadAppConfig, saveAppConfig, getAppConfigValue } from "@/lib/settings-storage";
import { Sparkles, Copy, RefreshCw, ChevronDown, ChevronUp, Loader2, AlertCircle, Check } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useTranslation } from "@/lib/i18n";

interface ResultsPanelProps {
  analysisResponse: AnalysisResponse;
  loading?: boolean;
}

interface AIAnalysisState {
  status: "idle" | "loading" | "streaming" | "complete" | "error";
  response: string;
  error?: string;
  executionTime?: number; // Time taken in seconds
}

export function ResultsPanel({ analysisResponse, loading }: ResultsPanelProps) {
  const { t } = useTranslation();
  const [aiStates, setAiStates] = useState<Record<string, AIAnalysisState>>({});
  const [promptTypes, setPromptTypes] = useState<Record<string, string>>({});
  const [customPrompts, setCustomPrompts] = useState<Record<string, string>>({});
  const [showAI, setShowAI] = useState<Record<string, boolean>>({});
  const [showCustomPrompt, setShowCustomPrompt] = useState<Record<string, boolean>>({});
  const [configErrors, setConfigErrors] = useState<Record<string, string>>({});
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});
  const [expandedInsights, setExpandedInsights] = useState<Record<string, boolean>>({});
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

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
      // Check cache first to avoid unnecessary API calls
      let appConfig = loadAppConfig();
      
      // If cache miss or expired, fetch from backend
      if (!appConfig) {
        appConfig = await apiClient.getAppConfig();
        // Cache the result
        saveAppConfig(appConfig);
      }
      
      if (!appConfig.ai_processing_enabled) {
        return {
          isValid: false,
          message: t("playground.enableAI") + ". " + t("playground.openSettings")
        };
      }
      
      // Check if AI config has API key and is configured
      const backendConfig = await getAIConfig();
      
      if (backendConfig.is_configured) {
        return { isValid: true };
      }
      
      // If not configured, check what's missing
      if (!backendConfig.api_key || backendConfig.api_key.trim() === "") {
        return {
          isValid: false,
          message: "AI API key is not configured. Please set it in settings."
        };
      }
      
      if (!backendConfig.base_url || backendConfig.base_url.trim() === "") {
        return {
          isValid: false,
          message: t("playground.setBaseURL") + ". " + t("playground.openSettings")
        };
      }
      
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

  const handleCopyResult = (insightId: string, pathIndex: number, content: string) => {
    navigator.clipboard.writeText(content);
    const key = `${insightId}_${pathIndex}`;
    setCopiedStates(prev => ({ ...prev, [key]: true }));
    setTimeout(() => {
      setCopiedStates(prev => ({ ...prev, [key]: false }));
    }, 2000);
  };

  const handleToggleAI = (insightId: string, pathIndex: number) => {
    const key = `${insightId}_${pathIndex}`;
    setShowAI(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleToggleExpand = (insightId: string, pathIndex: number) => {
    const key = `${insightId}_${pathIndex}`;
    setExpandedInsights(prev => ({ ...prev, [key]: !(prev[key] ?? true) }));
  };

  const handleToggleCard = (insightId: string) => {
    setExpandedCards(prev => ({ ...prev, [insightId]: !(prev[insightId] ?? true) }));
  };

  const handlePromptTypeChange = (insightId: string, pathIndex: number, value: string) => {
    const key = `${insightId}_${pathIndex}`;
    setPromptTypes(prev => ({ ...prev, [key]: value }));
    setShowCustomPrompt(prev => ({ ...prev, [key]: value === "custom" }));
  };

  const handleAIAnalyzeForPath = async (insightId: string, pathIndex: number, content: string) => {
    const key = `${insightId}_${pathIndex}`;
    // Clear any previous config errors for this path result
    setConfigErrors(prev => {
      const updated = { ...prev };
      delete updated[key];
      return updated;
    });

    // Check AI configuration before proceeding
    const configCheck = await checkAIConfiguration();
    if (!configCheck.isValid) {
      setConfigErrors(prev => ({
        ...prev,
        [key]: configCheck.message || "AI is not properly configured."
      }));
      setAiStates(prev => ({
        ...prev,
        [key]: {
          status: "error",
          response: "",
          error: configCheck.message || "Configuration error",
        }
      }));
      return;
    }

    const promptType = promptTypes[key] || "explain";
    const customPrompt = customPrompts[key];

    // Validate custom prompt if needed
    if (promptType === "custom" && (!customPrompt || customPrompt.trim() === "")) {
      setConfigErrors(prev => ({
        ...prev,
        [key]: "Please enter a custom prompt."
      }));
      setAiStates(prev => ({
        ...prev,
        [key]: {
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
      [key]: {
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
            [key]: {
              status: "streaming",
              response: fullResponse,
            }
          }));
        }
      );

      const executionTime = (Date.now() - startTime) / 1000;
      setAiStates(prev => ({
        ...prev,
        [key]: {
          status: "complete",
          response: fullResponse,
          executionTime,
        }
      }));
    } catch (error) {
      const executionTime = (Date.now() - startTime) / 1000;
      setAiStates(prev => ({
        ...prev,
        [key]: {
          status: "error",
          response: "",
          error: String(error),
          executionTime,
        }
      }));
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{t("results.analysisResults")}</h2>
      
      {/* Statistics Card */}
      <Card className="bg-gradient-to-br from-primary/10 via-primary/5 to-primary/10 dark:from-primary/20 dark:via-primary/15 dark:to-primary/20 border-2 border-primary/30 dark:border-primary/30">
        <CardHeader>
          <CardTitle className="text-base text-foreground dark:text-foreground">{t("results.analysisStatistics")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">{t("results.insightsRun")}</span>
              <span className="text-2xl font-bold text-primary dark:text-primary">{insights_count}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">{t("results.totalTime")}</span>
              <span className="text-2xl font-bold text-primary dark:text-primary">{formatTime(total_time)}</span>
            </div>
            <div className="flex flex-col sm:col-span-1">
              <span className="text-xs text-muted-foreground uppercase tracking-wide">{t("results.individualTimes")}</span>
              <div className="text-xs space-y-1 mt-1">
                {results.map((resultItem) => (
                  <div key={resultItem.insight_id} className="flex justify-between items-center gap-2">
                    <span className="text-foreground dark:text-foreground truncate flex-1 min-w-0" title={resultItem.insight_id}>
                      {resultItem.insight_id}
                    </span>
                    <span className="font-semibold text-primary dark:text-primary flex-shrink-0">
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
        {results.map((resultItem, insightIndex) => (
          <Card key={resultItem.insight_id} className="bg-gradient-to-br from-primary/10 via-primary/5 to-primary/10 dark:from-primary/20 dark:via-primary/15 dark:to-primary/20 border-2 border-primary/30 dark:border-primary/30">
            <CardHeader>
              <CardTitle 
                className="text-base flex justify-between items-center cursor-pointer select-none"
                onDoubleClick={() => handleToggleCard(resultItem.insight_id)}
                title="Double-click to expand/collapse"
              >
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleCard(resultItem.insight_id)}
                    className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
                    title={expandedCards[resultItem.insight_id] ?? true ? "Collapse (or double-click title)" : "Expand (or double-click title)"}
                  >
                    {expandedCards[resultItem.insight_id] ?? true ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronUp className="h-4 w-4" />
                    )}
                  </Button>
                  <span>{t("results.insight")}: {resultItem.insight_id}</span>
                  {resultItem.results.length > 1 && (
                    <Badge variant="secondary" className="text-xs">
                      {resultItem.results.length} path(s)
                    </Badge>
                  )}
                </div>
                <span className="text-xs font-normal text-muted-foreground">
                  {formatTime(resultItem.execution_time)}
                </span>
              </CardTitle>
            </CardHeader>
            {(expandedCards[resultItem.insight_id] ?? true) && (
            <CardContent>
              <div className="space-y-4">
                {/* Render each path result */}
                {resultItem.results.map((pathResult, pathIndex) => {
                  const userPath = pathResult.metadata?.user_path || `Path ${pathIndex + 1}`;
                  const pathKey = `${resultItem.insight_id}_${pathIndex}`;
                  
                  return (
                    <div key={pathIndex} className="border rounded-lg p-4 space-y-4">
                      {/* Path Header */}
                      <div className="flex items-center justify-between pb-2 border-b">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm">Path: {userPath}</span>
                        </div>
                      </div>
                      
                      {pathResult.result_type === "text" && (
                        <div className="space-y-4">
                          {/* Header with metadata and copy button */}
                          {pathResult.metadata && (
                            <div className="border border-primary/20 rounded-lg overflow-hidden">
                              {/* Header bar */}
                              <div 
                                className="bg-gradient-to-r from-primary/10 to-accent/10 px-4 py-3 border-b border-primary/20 flex items-center justify-between cursor-pointer select-none"
                                onDoubleClick={(e) => {
                                  if ((e.target as HTMLElement).closest('button')) {
                                    return;
                                  }
                                  handleToggleExpand(resultItem.insight_id, pathIndex);
                                }}
                                title="Double-click to expand/collapse content"
                              >
                                <div className="flex items-center gap-4 text-sm">
                                  {pathResult.metadata.line_count !== undefined && (
                                    <span className="text-foreground font-medium">
                                      {pathResult.metadata.line_count} {pathResult.metadata.line_count === 1 ? t("results.lineFound") : t("results.linesFound")}
                                    </span>
                                  )}
                                  {pathResult.metadata.truncated && (
                                    <span className="text-accent font-medium">
                                      (Truncated to {pathResult.metadata.truncated_to ?? pathResult.content.split('\n').length} lines)
                                    </span>
                                  )}
                                  {pathResult.metadata.total_lines !== undefined && pathResult.metadata.total_lines > (pathResult.metadata.truncated_to ?? pathResult.content.split('\n').length) && (
                                    <span className="text-muted-foreground text-xs">
                                      of {pathResult.metadata.total_lines} total
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleToggleExpand(resultItem.insight_id, pathIndex)}
                                    className="text-primary hover:bg-primary/10"
                                    title={expandedInsights[pathKey] ?? true ? "Minimize (or double-click header)" : "Expand (or double-click header)"}
                                  >
                                    {expandedInsights[pathKey] ?? true ? (
                                      <ChevronUp className="h-4 w-4" />
                                    ) : (
                                      <ChevronDown className="h-4 w-4" />
                                    )}
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleCopyResult(resultItem.insight_id, pathIndex, pathResult.content)}
                                    className="text-primary hover:bg-primary/10"
                                  >
                                    {copiedStates[pathKey] ? (
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
                              </div>

                              {/* Command display and Results - conditionally rendered */}
                              {(expandedInsights[pathKey] ?? true) && (
                                <>
                                  {/* Command display */}
                                  {pathResult.metadata.execution_command && (
                                    <div className="bg-muted px-4 py-2 border-b border-primary/20">
                                      <code className="text-xs text-muted-foreground font-mono">
                                        $ {pathResult.metadata.execution_command}
                                      </code>
                                    </div>
                                  )}

                                  {/* Results */}
                                  <div className="bg-primary/5 overflow-auto max-h-[600px] border-t border-primary/20">
                                    <pre className="p-4 text-sm font-mono text-foreground whitespace-pre-wrap">
                                      {pathResult.content.split('\n').map((line, index) => (
                                        <div key={index} className="flex hover:bg-primary/10">
                                          <span className="text-primary select-none mr-4 text-right w-12 flex-shrink-0 font-semibold">
                                            {index + 1}
                                          </span>
                                          <span className="flex-1">{line || ' '}</span>
                                        </div>
                                      ))}
                                    </pre>
                                  </div>
                                </>
                              )}
                            </div>
                          )}

                          {/* Fallback: Simple display if no metadata */}
                          {!pathResult.metadata && (
                            <div className="space-y-2">
                              <div 
                                className="flex items-center justify-between cursor-pointer select-none"
                                onDoubleClick={(e) => {
                                  if ((e.target as HTMLElement).closest('button')) {
                                    return;
                                  }
                                  handleToggleExpand(resultItem.insight_id, pathIndex);
                                }}
                                title="Double-click to expand/collapse content"
                              >
                                <span className="text-sm text-muted-foreground">
                                  Path result
                                </span>
                                <div className="flex items-center gap-2">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleToggleExpand(resultItem.insight_id, pathIndex)}
                                    className="text-primary hover:bg-primary/10"
                                    title={expandedInsights[pathKey] ?? true ? "Minimize (or double-click header)" : "Expand (or double-click header)"}
                                  >
                                    {expandedInsights[pathKey] ?? true ? (
                                      <ChevronUp className="h-4 w-4" />
                                    ) : (
                                      <ChevronDown className="h-4 w-4" />
                                    )}
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleCopyResult(resultItem.insight_id, pathIndex, pathResult.content)}
                                    className="text-primary hover:bg-primary/10"
                                  >
                                    {copiedStates[pathKey] ? (
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
                              </div>
                              {(expandedInsights[pathKey] ?? true) && (
                                <pre className="whitespace-pre-wrap rounded-md border border-border bg-muted p-4 font-mono text-sm overflow-x-auto overflow-y-auto max-h-[600px]">
                                  {pathResult.content}
                                </pre>
                              )}
                            </div>
                          )}

                          {/* Auto-triggered AI Analysis Card - Success */}
                          {pathResult.ai_analysis && (
                            <Card className="border-blue-500 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
                              <CardHeader className="pb-3">
                                <CardTitle className="text-sm flex items-center gap-2">
                                  <Sparkles className="h-4 w-4 text-blue-500" />
                                  <span>{t("playground.aiAnalysis")} (Auto)</span>
                                  <Badge variant="secondary" className="ml-auto text-xs">
                                    {pathResult.ai_prompt_type || "custom"}
                                  </Badge>
                                </CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap text-sm">
                                  {pathResult.ai_analysis}
                                </div>
                              </CardContent>
                            </Card>
                          )}

                          {/* Auto-triggered AI Analysis Card - Error */}
                          {pathResult.ai_analysis_error && (
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
                                    {pathResult.ai_analysis_error}
                                  </div>
                                  <p className="text-xs text-red-700 dark:text-red-300 mt-2">
                                    You can still manually analyze this result using the "Analyze with AI" section below with different settings or a shorter prompt.
                                  </p>
                                </div>
                              </CardContent>
                            </Card>
                          )}

                          {/* AI Analysis Section */}
                          {pathResult.ai_enabled && (
                            <div className="border-t pt-4">
                              <Button
                                onClick={() => handleToggleAI(resultItem.insight_id, pathIndex)}
                                className="mb-2 w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0 shadow-md hover:shadow-lg transition-all duration-200 font-bold relative"
                                size="sm"
                              >
                                <span className="flex items-center gap-2 justify-center">
                                  <Sparkles className="h-4 w-4 text-white" />
                                  {pathResult.ai_analysis ? t("playground.analyzeWithAI") + " (Re-analyze)" : t("playground.analyzeWithAI")}
                                </span>
                                <span className="absolute right-4">
                                  {showAI[pathKey] ? (
                                    <ChevronUp className="h-4 w-4 text-white" />
                                  ) : (
                                    <ChevronDown className="h-4 w-4 text-white" />
                                  )}
                                </span>
                              </Button>

                              {showAI[pathKey] && (
                                <div className="space-y-3 mt-3">
                                  {/* Configuration Error Alert */}
                                  {configErrors[pathKey] && (
                                    <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-950/30">
                                      <div className="flex items-start gap-3">
                                        <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                                        <div className="flex-1 space-y-2">
                                          <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                                            AI Configuration Required
                                          </p>
                                          <p className="text-sm text-amber-800 dark:text-amber-200">
                                            {configErrors[pathKey]}
                                          </p>
                                          <div className="text-xs text-amber-700 dark:text-amber-300 space-y-1">
                                            <p>To use AI analysis, please configure:</p>
                                            <ul className="list-disc list-inside space-y-0.5 ml-2">
                                              <li>Enable AI processing</li>
                                              <li>Set the AI Base URL (e.g., https://api.openai.com/v1)</li>
                                              <li>Provide your API Key</li>
                                            </ul>
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  )}

                                  {/* AI Analysis Type Dropdown and Analyze Button */}
                                  <div className="space-y-2">
                                    <Label htmlFor={`ai-prompt-type-${pathKey}`}>
                                      {t("promptManager.loadPreset")}
                                    </Label>
                                    <div className="flex items-center gap-2">
                                      <select
                                        id={`ai-prompt-type-${pathKey}`}
                                        value={promptTypes[pathKey] || "explain"}
                                        onChange={(e) =>
                                          handlePromptTypeChange(resultItem.insight_id, pathIndex, e.target.value)
                                        }
                                        className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                      >
                                        <option value="explain">{t("promptManager.explain")}</option>
                                        <option value="summarize">{t("promptManager.summarize")}</option>
                                        <option value="recommend">{t("promptManager.recommend")}</option>
                                        <option value="custom">Custom</option>
                                      </select>
                                      <Button
                                        onClick={() => handleAIAnalyzeForPath(resultItem.insight_id, pathIndex, pathResult.content)}
                                        disabled={aiStates[pathKey]?.status === "streaming"}
                                        size="sm"
                                        className="h-10 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white border-0 shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed font-bold whitespace-nowrap"
                                      >
                                        {aiStates[pathKey]?.status === "streaming" ? (
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
                                  </div>

                                  {/* Custom Prompt Textarea */}
                                  {showCustomPrompt[pathKey] && (
                                    <Textarea
                                      placeholder="Enter your custom prompt..."
                                      value={customPrompts[pathKey] || ""}
                                      onChange={(e) =>
                                        setCustomPrompts(prev => ({
                                          ...prev,
                                          [pathKey]: e.target.value
                                        }))
                                      }
                                      rows={3}
                                      className="text-sm"
                                    />
                                  )}

                                  {/* AI Response */}
                                  {aiStates[pathKey] && (
                                    <div className="rounded-md border border-blue-500 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20 p-4">
                                      {aiStates[pathKey].status === "error" ? (
                                        <div className="text-red-600 text-sm">
                                          Error: {aiStates[pathKey].error}
                                        </div>
                                      ) : aiStates[pathKey].response ? (
                                        <>
                                          <div className="flex justify-between items-start mb-2">
                                            <div className="flex items-center gap-2">
                                              <span className="text-xs font-semibold text-blue-700 dark:text-blue-300 uppercase">
                                                {t("playground.aiAnalysis")}
                                              </span>
                                              {aiStates[pathKey].executionTime !== undefined ? (
                                                <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                                                  ({formatTime(aiStates[pathKey].executionTime!)})
                                                </span>
                                              ) : aiStates[pathKey].status === "streaming" ? (
                                                <span className="text-xs text-blue-500 dark:text-blue-400">
                                                  (analyzing...)
                                                </span>
                                              ) : null}
                                            </div>
                                            <div className="flex gap-2">
                                              <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleCopyAI(aiStates[pathKey].response)}
                                              >
                                                <Copy className="h-3 w-3" />
                                              </Button>
                                              <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleAIAnalyzeForPath(resultItem.insight_id, pathIndex, pathResult.content)}
                                              >
                                                <RefreshCw className="h-3 w-3" />
                                              </Button>
                                            </div>
                                          </div>
                                          <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                                            {aiStates[pathKey].response}
                                            {aiStates[pathKey].status === "streaming" && (
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
                      {pathResult.result_type === "file" && (
                        <div className="text-sm text-muted-foreground">
                          File: {pathResult.content}
                        </div>
                      )}
                      {pathResult.result_type === "chart_data" && (
                        <div className="text-sm text-muted-foreground">
                          Chart data (JSON): <pre className="mt-2 whitespace-pre-wrap rounded-md border border-border bg-muted p-4 font-mono text-xs overflow-x-auto">{pathResult.content}</pre>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}

