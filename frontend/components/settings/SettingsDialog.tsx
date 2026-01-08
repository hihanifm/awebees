"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AISettings, loadAISettings, saveAISettings } from "@/lib/settings-storage";
import { getAIConfig, updateAIConfig, testAIConnection, apiClient } from "@/lib/api-client";
import { Settings, Loader2, CheckCircle2, XCircle, FolderOpen, X, RefreshCw, Palette, Languages, FileText } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { themes } from "@/lib/themes";
import { loadTheme, saveTheme } from "@/lib/theme-storage";
import { loadLanguage, saveLanguage, type Language } from "@/lib/language-storage";
import { useTranslation } from "@/lib/i18n";
import { loadLogLevel, saveLogLevel, type LogLevel } from "@/lib/logging-storage";
import { logger } from "@/lib/logger";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const { toast } = useToast();
  const [settings, setSettings] = useState<AISettings>({
    enabled: false,
    baseUrl: "https://api.openai.com/v1",
    apiKey: "sk-no-key-required",
    model: "gpt-4o-mini",
    maxTokens: 2000,
    temperature: 0.7,
  });

  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [testMessage, setTestMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Theme state
  const [selectedTheme, setSelectedTheme] = useState<string>("warm");
  
  // Language state
  const { t, language, setLanguage: setLanguageState } = useTranslation();
  const [selectedLanguage, setSelectedLanguage] = useState<Language>("en");

  // Insight paths state
  const [insightPaths, setInsightPaths] = useState<string[]>([]);
  const [newPath, setNewPath] = useState("");
  const [isLoadingPaths, setIsLoadingPaths] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Logging state
  const [backendLogLevel, setBackendLogLevel] = useState<string>("INFO");
  const [frontendLogLevel, setFrontendLogLevel] = useState<LogLevel>("INFO");
  const [isLoadingLogging, setIsLoadingLogging] = useState(false);

  // Model selection state
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [modelsSource, setModelsSource] = useState<'direct' | 'proxy' | 'defaults'>('defaults');
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        // Load from localStorage
        const localSettings = loadAISettings();
        logger.info("Loaded settings from localStorage:", localSettings);
        
        // Load from backend
        const backendConfig = await getAIConfig();
        logger.info("Loaded settings from backend:", backendConfig);
        
        // Merge: local overrides backend
        // For booleans, explicitly check if localStorage has a value
        const enabledValue = localSettings !== null && localSettings.hasOwnProperty('enabled') 
            ? localSettings.enabled 
            : (backendConfig.enabled ?? false);
        
        const merged: AISettings = {
          enabled: enabledValue,
          baseUrl: localSettings?.baseUrl ?? backendConfig.base_url ?? "https://api.openai.com/v1",
          apiKey: localSettings?.apiKey ?? backendConfig.api_key_preview ?? "",
          model: localSettings?.model ?? backendConfig.model ?? "gpt-4o-mini",
          maxTokens: localSettings?.maxTokens ?? backendConfig.max_tokens ?? 2000,
          temperature: localSettings?.temperature ?? backendConfig.temperature ?? 0.7,
        };
        
        logger.info("Merged AI settings:", merged);
        setSettings(merged);
      } catch (error) {
        logger.error("Failed to load AI settings:", error);
      }
    };
    
    const loadInsightPaths = async () => {
      setIsLoadingPaths(true);
      try {
        const paths = await apiClient.getInsightPaths();
        setInsightPaths(paths);
      } catch (error) {
        logger.error("Failed to load insight paths:", error);
        toast({
          title: "Error",
          description: "Failed to load external insight paths",
          variant: "destructive",
        });
      } finally {
        setIsLoadingPaths(false);
      }
    };

    const loadThemeSettings = () => {
      const savedTheme = loadTheme();
      setSelectedTheme(savedTheme);
    };

    const loadLanguageSettings = () => {
      const savedLanguage = loadLanguage();
      setSelectedLanguage(savedLanguage);
    };

    const loadLoggingSettings = async () => {
      setIsLoadingLogging(true);
      try {
        // Load backend log level
        const backendConfig = await apiClient.getLoggingConfig();
        setBackendLogLevel(backendConfig.log_level);

        // Load frontend log level
        const frontendLevel = loadLogLevel();
        setFrontendLogLevel(frontendLevel);
      } catch (error) {
        logger.error("Failed to load logging settings:", error);
      } finally {
        setIsLoadingLogging(false);
      }
    };

    const loadAvailableModels = async () => {
      // Only fetch if we have a base URL and API key
      const localSettings = loadAISettings();
      const baseUrl = localSettings?.baseUrl || settings.baseUrl;
      const apiKey = localSettings?.apiKey || settings.apiKey;

      if (!baseUrl || !apiKey) {
        // Use defaults if no config yet
        const defaultModels = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'];
        setAvailableModels(defaultModels);
        setModelsSource('defaults');
        // Set first model as default if no model selected
        // Use functional form to avoid stale state closure
        setSettings(prev => {
          if (!prev.model && defaultModels.length > 0) {
            return { ...prev, model: defaultModels[0] };
          }
          return prev;
        });
        return;
      }

      setIsLoadingModels(true);
      try {
        const result = await apiClient.getAvailableModels(baseUrl, apiKey);
        setAvailableModels(result.models);
        setModelsSource(result.source);
        
        // Automatically select first model if current model is not in the list
        // Use functional form to avoid stale state closure
        if (result.models.length > 0) {
          setSettings(prev => {
            const currentModelExists = result.models.includes(prev.model);
            if (!currentModelExists) {
              return { ...prev, model: result.models[0] };
            }
            return prev;
          });
        }
        
        logger.info(`Loaded ${result.models.length} models via ${result.source}`);
      } catch (error) {
        logger.error("Failed to load available models:", error);
        // Fall back to defaults
        const defaultModels = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'];
        setAvailableModels(defaultModels);
        setModelsSource('defaults');
      } finally {
        setIsLoadingModels(false);
      }
    };
    
    if (open) {
      loadSettings();
      loadInsightPaths();
      loadThemeSettings();
      loadLanguageSettings();
      loadLoggingSettings();
      loadAvailableModels();
    }
  }, [open]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      logger.info("Saving AI settings:", settings);
      
      // Save to localStorage
      saveAISettings(settings);
      logger.info("Settings saved to localStorage");
      
      // Send to backend
      await updateAIConfig({
        enabled: settings.enabled,
        base_url: settings.baseUrl,
        api_key: settings.apiKey,
        model: settings.model,
        max_tokens: settings.maxTokens,
        temperature: settings.temperature,
      });
      logger.info("Settings saved to backend");
      
      toast({
        title: t("settings.saved"),
        description: t("settings.saved"),
      });
      
      // Only close dialog if save was successful
      onOpenChange(false);
    } catch (error) {
      logger.error("Failed to save settings:", error);
      toast({
        title: t("common.error"),
        description: t("settings.saveFailed"),
        variant: "destructive",
      });
      // Don't close dialog on error so user can try again
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    setTestStatus("testing");
    setTestMessage(t("settings.testing"));
    
    try {
      // Test with CURRENT form values, not saved values
      const result = await apiClient.testAIConnectionWithConfig({
        enabled: settings.enabled,
        base_url: settings.baseUrl,
        api_key: settings.apiKey,
        model: settings.model,
        max_tokens: settings.maxTokens,
        temperature: settings.temperature,
      });
      
      if (result.success) {
        setTestStatus("success");
        setTestMessage(t("settings.connectionSuccess"));
      } else {
        setTestStatus("error");
        setTestMessage(result.message || t("settings.connectionFailed"));
      }
    } catch (error) {
      setTestStatus("error");
      setTestMessage(t("settings.connectionFailed") + ": " + String(error));
    }
  };

  const handleAddPath = async () => {
    if (!newPath.trim()) {
      toast({
        title: "Error",
        description: "Please enter a valid path",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await apiClient.addInsightPath(newPath.trim());
      setInsightPaths([...insightPaths, newPath.trim()]);
      setNewPath("");
      toast({
        title: "Success",
        description: `Added path: ${newPath.trim()}. Found ${result.insights_count} total insights.`,
      });
    } catch (error) {
      logger.error("Failed to add insight path:", error);
      toast({
        title: "Error",
        description: String(error),
        variant: "destructive",
      });
    }
  };

  const handleRemovePath = async (path: string) => {
    try {
      const result = await apiClient.removeInsightPath(path);
      setInsightPaths(insightPaths.filter((p) => p !== path));
      toast({
        title: "Success",
        description: `Removed path: ${path}. ${result.insights_count} insights remaining.`,
      });
    } catch (error) {
      logger.error("Failed to remove insight path:", error);
      toast({
        title: "Error",
        description: String(error),
        variant: "destructive",
      });
    }
  };

  const handleRefreshInsights = async () => {
    setIsRefreshing(true);
    try {
      const result = await apiClient.refreshInsights();
      toast({
        title: "Success",
        description: `Refreshed ${result.insights_count} insights`,
      });
    } catch (error) {
      logger.error("Failed to refresh insights:", error);
      toast({
        title: "Error",
        description: String(error),
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleThemeChange = (newTheme: string) => {
    setSelectedTheme(newTheme);
    saveTheme(newTheme);
    
    // Apply theme immediately to html element
    if (typeof document !== "undefined") {
      const htmlElement = document.documentElement;
      htmlElement.classList.remove("theme-warm", "theme-purple", "theme-blue", "theme-green");
      htmlElement.classList.add(`theme-${newTheme}`);
    }

    toast({
      title: "Theme Updated",
      description: `Switched to ${themes.find(t => t.id === newTheme)?.name} theme`,
    });
  };

  const handleLanguageChange = (newLanguage: Language) => {
    setSelectedLanguage(newLanguage);
    saveLanguage(newLanguage);
    setLanguageState(newLanguage);
    
    // Apply language immediately to html element
    if (typeof document !== "undefined") {
      document.documentElement.lang = newLanguage;
    }

    toast({
      title: "Language Updated",
      description: `Switched to ${newLanguage === "ko" ? "한국어" : "English"}`,
    });
  };

  const handleBackendLogLevelChange = async (newLevel: string) => {
    try {
      await apiClient.updateLoggingConfig(newLevel);
      setBackendLogLevel(newLevel);
      toast({
        title: "Success",
        description: `Backend log level updated to ${newLevel}`,
      });
    } catch (error) {
      logger.error("Failed to update backend log level:", error);
      toast({
        title: "Error",
        description: "Failed to update backend log level",
        variant: "destructive",
      });
    }
  };

  const handleFrontendLogLevelChange = (newLevel: LogLevel) => {
    setFrontendLogLevel(newLevel);
    saveLogLevel(newLevel);
    logger.setLevel(newLevel);
    toast({
      title: "Success",
      description: `Frontend log level updated to ${newLevel}`,
    });
  };

  const handleRefreshModels = async () => {
    if (!settings.baseUrl || !settings.apiKey) {
      toast({
        title: "Error",
        description: "Please enter Base URL and API Key first",
        variant: "destructive",
      });
      return;
    }

    setIsLoadingModels(true);
    try {
      const result = await apiClient.getAvailableModels(settings.baseUrl, settings.apiKey);
      setAvailableModels(result.models);
      setModelsSource(result.source);
      
      // Automatically select first model if current model is not in the list
      // Use functional form to avoid stale state closure
      if (result.models.length > 0) {
        setSettings(prev => {
          const currentModelExists = result.models.includes(prev.model);
          if (!currentModelExists) {
            return { ...prev, model: result.models[0] };
          }
          return prev;
        });
      }
      
      const sourceText = result.source === 'direct' ? 'direct connection' : 
                        result.source === 'proxy' ? 'backend proxy' : 'defaults';
      
      toast({
        title: "Models Refreshed",
        description: `Loaded ${result.models.length} models via ${sourceText}`,
      });
    } catch (error) {
      logger.error("Failed to refresh models:", error);
      toast({
        title: "Error",
        description: "Failed to refresh models",
        variant: "destructive",
      });
    } finally {
      setIsLoadingModels(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            {t("settings.title")}
          </DialogTitle>
          <DialogDescription>
            {t("settings.description")}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="ai" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="ai">{t("settings.ai")}</TabsTrigger>
            <TabsTrigger value="insights">{t("settings.insights")}</TabsTrigger>
            <TabsTrigger value="logging">Logging</TabsTrigger>
            <TabsTrigger value="general">{t("settings.general")}</TabsTrigger>
          </TabsList>

          <TabsContent value="ai" className="space-y-4 mt-4">
            {/* AI Enabled Toggle */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="ai-enabled">{t("settings.aiEnabled")}</Label>
                <p className="text-sm text-muted-foreground">
                  {t("settings.aiEnabledHint")}
                </p>
              </div>
              <Switch
                id="ai-enabled"
                checked={settings.enabled}
                onCheckedChange={(checked) =>
                  setSettings({ ...settings, enabled: checked })
                }
              />
            </div>

            {/* Base URL */}
            <div className="space-y-2">
              <Label htmlFor="base-url">{t("settings.baseURL")}</Label>
              <Input
                id="base-url"
                value={settings.baseUrl}
                onChange={(e) =>
                  setSettings({ ...settings, baseUrl: e.target.value })
                }
                placeholder="https://api.openai.com/v1"
                disabled={!settings.enabled}
              />
              <p className="text-xs text-muted-foreground">
                {t("settings.baseURLHint")}
              </p>
            </div>

            {/* API Key */}
            <div className="space-y-2">
              <Label htmlFor="api-key">{t("settings.apiKey")}</Label>
              <Input
                id="api-key"
                type="password"
                value={settings.apiKey}
                onChange={(e) =>
                  setSettings({ ...settings, apiKey: e.target.value })
                }
                placeholder="sk-..."
                disabled={!settings.enabled}
              />
              <p className="text-xs text-muted-foreground">
                {t("settings.apiKeyHint")}
              </p>
            </div>

            {/* Model Selection */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="model">{t("settings.model")}</Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRefreshModels}
                  disabled={!settings.enabled || isLoadingModels || !settings.baseUrl}
                  className="h-7 px-2"
                >
                  {isLoadingModels ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3 w-3" />
                  )}
                  <span className="ml-1 text-xs">Refresh</span>
                </Button>
              </div>
              <Select
                value={settings.model}
                onValueChange={(value) =>
                  setSettings({ ...settings, model: value })
                }
                disabled={!settings.enabled || isLoadingModels}
              >
                <SelectTrigger id="model">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {availableModels.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {modelsSource === 'direct' && `✓ ${availableModels.length} models loaded (direct connection)`}
                  {modelsSource === 'proxy' && `✓ ${availableModels.length} models loaded via proxy`}
                  {modelsSource === 'defaults' && `⚠ Using default models (server unreachable)`}
                </p>
              )}
            </div>

            {/* Max Tokens */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="max-tokens">{t("settings.maxTokens")}</Label>
                <span className="text-sm text-muted-foreground">
                  {settings.maxTokens}
                </span>
              </div>
              <Slider
                id="max-tokens"
                min={100}
                max={4000}
                step={100}
                value={[settings.maxTokens]}
                onValueChange={([value]) =>
                  setSettings({ ...settings, maxTokens: value })
                }
                disabled={!settings.enabled}
              />
            </div>

            {/* Temperature */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="temperature">{t("settings.temperature")}</Label>
                <span className="text-sm text-muted-foreground">
                  {settings.temperature.toFixed(1)}
                </span>
              </div>
              <Slider
                id="temperature"
                min={0}
                max={2}
                step={0.1}
                value={[settings.temperature]}
                onValueChange={([value]) =>
                  setSettings({ ...settings, temperature: value })
                }
                disabled={!settings.enabled}
              />
              <p className="text-xs text-muted-foreground">
                {t("settings.temperatureHint")}
              </p>
            </div>

            {/* Test Connection */}
            <div className="space-y-2">
              <Button
                variant="outline"
                onClick={handleTest}
                disabled={!settings.enabled || !settings.apiKey || testStatus === "testing"}
                className="w-full font-bold"
              >
                {testStatus === "testing" && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {testStatus === "success" && (
                  <CheckCircle2 className="mr-2 h-4 w-4 text-green-500" />
                )}
                {testStatus === "error" && (
                  <XCircle className="mr-2 h-4 w-4 text-red-500" />
                )}
                {t("settings.testConnection")}
              </Button>
              {testMessage && (
                <p
                  className={`text-xs ${
                    testStatus === "success" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {testMessage}
                </p>
              )}
            </div>
          </TabsContent>

          <TabsContent value="insights" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>{t("settings.insightPaths")}</Label>
              <p className="text-sm text-muted-foreground">
                {t("settings.insightPathsHint")}
              </p>
              
              {/* List of paths */}
              {isLoadingPaths ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              ) : insightPaths.length > 0 ? (
                <div className="space-y-2">
                  {insightPaths.map((path, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 rounded border bg-muted/50">
                      <FolderOpen className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                      <span className="flex-1 text-sm truncate font-mono">{path}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemovePath(path)}
                        className="h-7 w-7 p-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-sm text-muted-foreground border border-dashed rounded-lg">
                  {t("settings.noPaths")}
                </div>
              )}
              
              {/* Add new path */}
              <div className="flex gap-2">
                <Input
                  placeholder={t("settings.pathPlaceholder")}
                  value={newPath}
                  onChange={(e) => setNewPath(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleAddPath();
                    }
                  }}
                  className="font-mono"
                />
                <Button onClick={handleAddPath} variant="secondary" className="font-bold">
                  {t("settings.addPath")}
                </Button>
              </div>
              
              {/* Refresh button */}
              <Button
                variant="outline"
                onClick={handleRefreshInsights}
                disabled={isRefreshing}
                className="w-full font-bold"
              >
                {isRefreshing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                {isRefreshing ? t("settings.refreshing") : t("settings.refresh")}
              </Button>
              <p className="text-xs text-muted-foreground">
                {t("settings.refreshInsightsHint")}
              </p>
            </div>
          </TabsContent>

          <TabsContent value="logging" className="space-y-4 mt-4">
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="h-5 w-5" />
                <h3 className="text-lg font-semibold">Logging Configuration</h3>
              </div>
              
              <p className="text-sm text-muted-foreground">
                Control logging verbosity for debugging and troubleshooting. Changes take effect immediately.
              </p>

              {isLoadingLogging ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <>
                  {/* Backend Log Level */}
                  <div className="space-y-2">
                    <Label htmlFor="backend-log-level">Backend Log Level</Label>
                    <Select value={backendLogLevel} onValueChange={handleBackendLogLevelChange}>
                      <SelectTrigger id="backend-log-level">
                        <SelectValue placeholder="Select backend log level" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="DEBUG">DEBUG - Detailed diagnostic info</SelectItem>
                        <SelectItem value="INFO">INFO - General informational messages</SelectItem>
                        <SelectItem value="WARNING">WARNING - Warning messages only</SelectItem>
                        <SelectItem value="ERROR">ERROR - Error messages only</SelectItem>
                        <SelectItem value="CRITICAL">CRITICAL - Critical errors only</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Controls Python backend logging. Persists to .env file.
                    </p>
                  </div>

                  {/* Frontend Log Level */}
                  <div className="space-y-2">
                    <Label htmlFor="frontend-log-level">Frontend Log Level</Label>
                    <Select value={frontendLogLevel} onValueChange={(value) => handleFrontendLogLevelChange(value as LogLevel)}>
                      <SelectTrigger id="frontend-log-level">
                        <SelectValue placeholder="Select frontend log level" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="DEBUG">DEBUG - All console output</SelectItem>
                        <SelectItem value="INFO">INFO - Info, warnings, and errors</SelectItem>
                        <SelectItem value="WARN">WARN - Warnings and errors only</SelectItem>
                        <SelectItem value="ERROR">ERROR - Errors only</SelectItem>
                        <SelectItem value="NONE">NONE - No console output</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Controls browser console logging. Saved to localStorage.
                    </p>
                  </div>

                  {/* Log Level Info */}
                  <div className="rounded-lg border p-4 space-y-2 bg-muted/50">
                    <p className="text-sm font-medium">Current Levels</p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-muted-foreground">Backend:</span>
                        <span className="ml-2 font-mono font-semibold">{backendLogLevel}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Frontend:</span>
                        <span className="ml-2 font-mono font-semibold">{frontendLogLevel}</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </TabsContent>

          <TabsContent value="general" className="space-y-4 mt-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Languages className="h-4 w-4" />
                  <Label htmlFor="language">{t("settings.language")}</Label>
                </div>
                <Select value={selectedLanguage} onValueChange={(value) => handleLanguageChange(value as Language)}>
                  <SelectTrigger id="language">
                    <SelectValue placeholder={t("settings.language")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">{t("settings.english")}</SelectItem>
                    <SelectItem value="ko">{t("settings.korean")}</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {t("settings.language")} - {selectedLanguage === "ko" ? "한국어" : "English"}
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Palette className="h-4 w-4" />
                  <Label htmlFor="theme">Color Theme</Label>
                </div>
                <Select value={selectedTheme} onValueChange={handleThemeChange}>
                  <SelectTrigger id="theme">
                    <SelectValue placeholder="Select theme" />
                  </SelectTrigger>
                  <SelectContent>
                    {themes.map((theme) => (
                      <SelectItem key={theme.id} value={theme.id}>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-4 h-4 rounded-full border border-border"
                            style={{ backgroundColor: theme.preview }}
                          />
                          <span>{theme.name}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {t("settings.themeHint")}
                </p>
              </div>

              {/* Theme preview */}
              <div className="rounded-lg border p-4 space-y-2">
                <p className="text-sm font-medium">Theme Preview</p>
                <div className="flex gap-2">
                  <div className="flex-1 h-12 rounded bg-primary flex items-center justify-center text-primary-foreground text-xs">
                    Primary
                  </div>
                  <div className="flex-1 h-12 rounded bg-secondary flex items-center justify-center text-secondary-foreground text-xs">
                    Secondary
                  </div>
                  <div className="flex-1 h-12 rounded bg-accent flex items-center justify-center text-accent-foreground text-xs">
                    Accent
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-bold">
            {t("common.cancel")}
          </Button>
          <Button onClick={handleSave} disabled={isSaving} className="font-bold">
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isSaving ? t("settings.saving") : t("settings.save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

