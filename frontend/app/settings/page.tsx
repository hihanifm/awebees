"use client";

import { useState, useEffect } from "react";
import { Loader2, CheckCircle2, XCircle, FolderOpen, X, RefreshCw, Palette, Languages, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AISettings, loadAISettings, saveAISettings, loadResultMaxLines, saveResultMaxLines, saveAppConfig, saveAllAIConfigs, clearAllAIConfigs, clearAISettings, loadAppConfig } from "@/lib/settings-storage";
import { getAIConfig, updateAIConfig, apiClient } from "@/lib/api-client";
import { useToast } from "@/components/ui/use-toast";
import { themes } from "@/lib/themes";
import { loadTheme, saveTheme } from "@/lib/theme-storage";
import { loadLanguage, saveLanguage, type Language } from "@/lib/language-storage";
import { useTranslation } from "@/lib/i18n";
import { loadLogLevel, saveLogLevel, type LogLevel } from "@/lib/logging-storage";
import { logger } from "@/lib/logger";

export default function SettingsPage() {
  const { toast } = useToast();
  const { t, setLanguage: setLanguageState } = useTranslation();
  const [settings, setSettings] = useState<AISettings>({
    // No defaults - will be loaded from backend, empty if no config exists
    baseUrl: "",
    apiKey: "",
    model: "",
    maxTokens: 0,
    temperature: 0,
  });
  const [configName, setConfigName] = useState<string>("");
  const [allConfigNames, setAllConfigNames] = useState<string[]>([]);
  const [isLoadingConfigs, setIsLoadingConfigs] = useState(false);
  const [showSaveAsDialog, setShowSaveAsDialog] = useState(false);
  const [newConfigName, setNewConfigName] = useState<string>("");
  const [isSavingAs, setIsSavingAs] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [testMessage, setTestMessage] = useState("");

  // Theme state
  const [selectedTheme, setSelectedTheme] = useState<string>("warm");
  
  // Language state
  const [selectedLanguage, setSelectedLanguage] = useState<Language>("en");

  // Insight paths state
  const [insightPaths, setInsightPaths] = useState<string[]>([]);
  const [newPath, setNewPath] = useState("");
  const [isLoadingPaths, setIsLoadingPaths] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Default repository state
  const [defaultRepository, setDefaultRepository] = useState<string | null>(null);
  const [isLoadingDefaultRepo, setIsLoadingDefaultRepo] = useState(false);

  // Logging state
  const [backendLogLevel, setBackendLogLevel] = useState<string>("INFO");
  const [frontendLogLevel, setFrontendLogLevel] = useState<LogLevel>("INFO");
  const [isLoadingLogging, setIsLoadingLogging] = useState(false);
  const [httpLogging, setHttpLogging] = useState<boolean>(true);
  const [aiDetailedLogging, setAiDetailedLogging] = useState<boolean>(true);
  const [aiStreamingEnabled, setAiStreamingEnabled] = useState<boolean>(true);
  
  // Global AI processing enabled state (separate from AI configs)
  const [aiProcessingEnabled, setAiProcessingEnabled] = useState<boolean>(true);

  // Model selection state
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [modelsSource, setModelsSource] = useState<'proxy' | 'error'>('proxy');
  const [isLoadingModels, setIsLoadingModels] = useState(false);

  // Result max lines state
  const [resultMaxLines, setResultMaxLines] = useState<number>(500);
  const [isLoadingResultMaxLines, setIsLoadingResultMaxLines] = useState(false);

  // Load settings on mount
  useEffect(() => {
    const loadAllConfigs = async () => {
      setIsLoadingConfigs(true);
      try {
        const result = await apiClient.getAllAIConfigs();
        const names = Object.keys(result.configs || {});
        setAllConfigNames(names);
        logger.info("Loaded AI config names:", names);
        return result; // Return the result to share it
      } catch (error) {
        logger.error("Failed to load AI configs:", error);
        setAllConfigNames([]);
        return null;
      } finally {
        setIsLoadingConfigs(false);
      }
    };

    const loadSettings = async (allConfigs: any) => {
      try {
        // Use backend configs directly - no localStorage merging needed
        let backendConfig: any = null;
        if (allConfigs) {
          const activeName = allConfigs.active_config_name;
          
          if (activeName && allConfigs.configs && allConfigs.configs[activeName]) {
            backendConfig = allConfigs.configs[activeName];
            setConfigName(activeName);
            logger.info("Loaded settings from backend:", backendConfig);
          } else {
            logger.warn("No active config found, using defaults");
            setConfigName("");
          }
        } else {
          logger.warn("No configs available, using defaults");
          setConfigName("");
        }
        
        // Use backend values directly - no defaults, honor backend exactly
        // Note: enabled removed - use global aiProcessingEnabled state instead
        const merged: AISettings = {
          baseUrl: backendConfig?.base_url ?? "",
          apiKey: backendConfig?.api_key ?? "",
          model: backendConfig?.model ?? "",
          maxTokens: backendConfig?.max_tokens ?? 0,
          temperature: backendConfig?.temperature ?? 0,
        };
        
        logger.info("Loaded AI settings from backend:", merged);
        setSettings(merged);
        
        // Save to in-memory cache so checkAIConfiguration can use it
        if (backendConfig) {
          saveAISettings(merged);
        }
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

    const loadDefaultRepository = async () => {
      setIsLoadingDefaultRepo(true);
      try {
        const repo = await apiClient.getDefaultRepository();
        setDefaultRepository(repo);
      } catch (error) {
        logger.error("Failed to load default repository:", error);
        toast({
          title: "Error",
          description: "Failed to load default repository",
          variant: "destructive",
        });
      } finally {
        setIsLoadingDefaultRepo(false);
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

    const loadLoggingSettings = async (allConfigs: any) => {
      setIsLoadingLogging(true);
      try {
        // Load all app config (cached in memory) - single API call for all config.json settings
        const appConfig = await apiClient.getAppConfig();
        
        // Use cached config values
        setBackendLogLevel(appConfig.log_level);
        setHttpLogging(appConfig.http_logging);
        setAiProcessingEnabled(appConfig.ai_processing_enabled);
        
        // Load frontend log level (not in config.json, it's frontend-only)
        const frontendLevel = loadLogLevel();
        setFrontendLogLevel(frontendLevel);

        // Load AI detailed logging config (now unified with app-config)
        setAiDetailedLogging(appConfig.detailed_logging);
        
        // Load AI streaming config - use shared configs result
        if (allConfigs) {
          const activeName = allConfigs.active_config_name;
          if (activeName && allConfigs.configs && allConfigs.configs[activeName]) {
            setAiStreamingEnabled(allConfigs.configs[activeName].streaming_enabled ?? true);
          } else {
            setAiStreamingEnabled(true);
          }
        } else {
          setAiStreamingEnabled(true);
        }
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
        // Keep empty if no config yet
        setAvailableModels([]);
        setModelsSource('proxy');
        return;
      }

      // Only fetch models if AI processing is globally enabled
      if (!aiProcessingEnabled) {
        // Keep empty if AI processing is disabled
        setAvailableModels([]);
        setModelsSource('proxy');
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
        // Keep empty on error
        setAvailableModels([]);
        setModelsSource('error');
      } finally {
        setIsLoadingModels(false);
      }
    };
    
    // Load everything in sequence to share the configs result
    (async () => {
      // Load AI configs first (shared across multiple functions)
      const allConfigs = await loadAllConfigs();
      
      // Load all other settings in parallel (but wait for configs first)
      await Promise.all([
        loadSettings(allConfigs),
        loadInsightPaths(),
        loadDefaultRepository(),
        Promise.resolve(loadThemeSettings()),
        Promise.resolve(loadLanguageSettings()),
        loadLoggingSettings(allConfigs),
        loadResultMaxLinesSettings(),
      ]);
      
      // Don't automatically fetch models from API - only when user clicks refresh
      // Keep models empty initially - will be populated when user clicks refresh
      setAvailableModels([]);
      setModelsSource('proxy');
    })();
  }, []);

  const loadResultMaxLinesSettings = async () => {
    setIsLoadingResultMaxLines(true);
    try {
      // Check cache first (from unified app config) - apiClient.getAppConfig() handles cache automatically
      const appConfig = await apiClient.getAppConfig();
      
      // Use cached value
      setResultMaxLines(appConfig.result_max_lines);
      
      // Also check localStorage for backward compatibility
      const localValue = loadResultMaxLines();
      
      // If localStorage has a different value, sync it
      if (localValue !== null && localValue !== appConfig.result_max_lines) {
        // Update backend to match localStorage (user preference) using unified config API
        try {
          await apiClient.updateAppConfig({ result_max_lines: localValue });
          // Refresh cache - apiClient.updateAppConfig() handles cache automatically
          const freshConfig = await apiClient.getAppConfig();
          setResultMaxLines(freshConfig.result_max_lines);
        } catch (error) {
          logger.error("Failed to sync result max lines:", error);
        }
      }
    } catch (error) {
      logger.error("Failed to load result max lines settings:", error);
      // Fallback to cached value or default
      const cached = loadAppConfig();
      setResultMaxLines(cached?.result_max_lines ?? 500);
    } finally {
      setIsLoadingResultMaxLines(false);
    }
  };

  const handleUpdate = async () => {
    if (!configName) {
      toast({
        title: t("common.error"),
        description: "No config selected to update",
        variant: "destructive",
      });
      return;
    }

    setIsUpdating(true);
    try {
      logger.info("Updating AI config:", settings);
      
      // Update the currently selected config (not necessarily active)
      // Note: enabled removed - use global aiProcessingEnabled state instead
      await apiClient.updateAIConfig({
        base_url: settings.baseUrl,
        api_key: settings.apiKey,
        model: settings.model,
        max_tokens: settings.maxTokens,
        temperature: settings.temperature,
        streaming_enabled: aiStreamingEnabled,
      }, configName);
      logger.info("Config updated");
      
      // Update in-memory cache - reload from server to get latest state (cache handled automatically)
      const allConfigs = await apiClient.getAllAIConfigs();
      if (allConfigs.configs[configName]) {
        const updatedConfig = allConfigs.configs[configName];
        const updatedSettings: AISettings = {
          baseUrl: updatedConfig.base_url ?? "",
          apiKey: updatedConfig.api_key ?? "",
          model: updatedConfig.model ?? "",
          maxTokens: updatedConfig.max_tokens ?? 0,
          temperature: updatedConfig.temperature ?? 0,
        };
        saveAISettings(updatedSettings);
      }
      
      toast({
        title: t("settings.saved"),
        description: `Config '${configName}' updated`,
      });
    } catch (error) {
      logger.error("Failed to update config:", error);
      toast({
        title: t("common.error"),
        description: `Failed to update config: ${String(error)}`,
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!configName) {
      toast({
        title: t("common.error"),
        description: "No active config to delete",
        variant: "destructive",
      });
      return;
    }

    if (!confirm(`Are you sure you want to delete config '${configName}'?`)) {
      return;
    }

    setIsDeleting(true);
    try {
      await apiClient.deleteAIConfig(configName);
      logger.info("Config deleted");
      
      // Clear cache and reload configs list - apiClient.getAllAIConfigs() handles cache automatically
      clearAllAIConfigs();
      clearAISettings();
      const result = await apiClient.getAllAIConfigs();
      const names = Object.keys(result.configs || {});
      setAllConfigNames(names);
      
      // If there are other configs, activate the first one
      if (names.length > 0) {
        await apiClient.activateAIConfig(names[0]);
        setConfigName(names[0]);
        const allConfigs = await apiClient.getAllAIConfigs();
        const activeConfig = allConfigs.configs[names[0]];
        if (activeConfig) {
          // Note: enabled removed - use global aiProcessingEnabled state instead
          // Honor backend values exactly - no defaults
          const newSettings = {
            baseUrl: activeConfig.base_url ?? "",
            apiKey: activeConfig.api_key ?? "",
            model: activeConfig.model ?? "",
            maxTokens: activeConfig.max_tokens ?? 0,
            temperature: activeConfig.temperature ?? 0,
          };
          setSettings(newSettings);
          setAiStreamingEnabled(activeConfig.streaming_enabled ?? true);
          // Save to in-memory cache
          saveAISettings(newSettings);
        }
      } else {
        setConfigName("");
        // Reset to empty - no defaults, honor backend
        // Note: enabled removed - use global aiProcessingEnabled state instead
        setSettings({
          baseUrl: "",
          apiKey: "",
          model: "",
          maxTokens: 0,
          temperature: 0,
        });
        setAiStreamingEnabled(true);
      }
      
      toast({
        title: "Success",
        description: `Config '${configName}' deleted`,
      });
    } catch (error) {
      logger.error("Failed to delete config:", error);
      toast({
        title: t("common.error"),
        description: `Failed to delete config: ${String(error)}`,
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleSaveAs = async () => {
    if (!newConfigName.trim()) {
      toast({
        title: t("common.error"),
        description: "Please enter a config name",
        variant: "destructive",
      });
      return;
    }

    if (allConfigNames.includes(newConfigName.trim())) {
      toast({
        title: t("common.error"),
        description: `Config '${newConfigName.trim()}' already exists`,
        variant: "destructive",
      });
      return;
    }

    setIsSavingAs(true);
    try {
      // Note: enabled removed - use global aiProcessingEnabled state instead
      await apiClient.createAIConfig({
        name: newConfigName.trim(),
        base_url: settings.baseUrl,
        api_key: settings.apiKey,
        model: settings.model,
        max_tokens: settings.maxTokens,
        temperature: settings.temperature,
        timeout: 60,
        streaming_enabled: aiStreamingEnabled,
      });
      
      // Reload configs list - apiClient.getAllAIConfigs() handles cache automatically
      const result = await apiClient.getAllAIConfigs();
      const names = Object.keys(result.configs || {});
      setAllConfigNames(names);
      
      // Activate the new config
      await apiClient.activateAIConfig(newConfigName.trim());
      setConfigName(newConfigName.trim());
      
      // Reload configs to update cache with the new config - apiClient.getAllAIConfigs() handles cache automatically
      const allConfigs = await apiClient.getAllAIConfigs();
      if (allConfigs.configs[newConfigName.trim()]) {
        const newConfig = allConfigs.configs[newConfigName.trim()];
        const newSettings: AISettings = {
          baseUrl: newConfig.base_url ?? "",
          apiKey: newConfig.api_key ?? "",
          model: newConfig.model ?? "",
          maxTokens: newConfig.max_tokens ?? 0,
          temperature: newConfig.temperature ?? 0,
        };
        saveAISettings(newSettings);
      }
      
      setShowSaveAsDialog(false);
      setNewConfigName("");
      
      toast({
        title: "Success",
        description: `Config '${newConfigName.trim()}' created and activated`,
      });
    } catch (error) {
      logger.error("Failed to save config:", error);
      toast({
        title: t("common.error"),
        description: `Failed to save config: ${String(error)}`,
        variant: "destructive",
      });
    } finally {
      setIsSavingAs(false);
    }
  };

  const handleTest = async () => {
    setTestStatus("testing");
    setTestMessage(t("settings.testing"));
    
    try {
      // Test with CURRENT form values, not saved values (including streaming setting)
      // Note: enabled removed - use global aiProcessingEnabled state instead
      const result = await apiClient.testAIConnectionWithConfig({
        base_url: settings.baseUrl,
        api_key: settings.apiKey,
        model: settings.model,
        max_tokens: settings.maxTokens,
        temperature: settings.temperature,
        streaming_enabled: aiStreamingEnabled,
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
      
      // Refresh insights to ensure all new insights and samples are loaded
      const refreshResult = await apiClient.refreshInsights();
      
      toast({
        title: "Success",
        description: `Added path: ${newPath.trim()}. Found ${refreshResult.insights_count} total insights.`,
      });
      // Dispatch event to refresh insights in InsightList
      window.dispatchEvent(new CustomEvent('insights-refreshed'));
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
      
      // Refresh insights to ensure all insights and samples are updated
      const refreshResult = await apiClient.refreshInsights();
      
      toast({
        title: "Success",
        description: `Removed path: ${path}. ${refreshResult.insights_count} insights remaining.`,
      });
      // Dispatch event to refresh insights in InsightList
      window.dispatchEvent(new CustomEvent('insights-refreshed'));
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
      // Dispatch event to refresh insights in InsightList
      window.dispatchEvent(new CustomEvent('insights-refreshed'));
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

  const handleSaveDefaultRepository = async () => {
    const pathToSave = defaultRepository?.trim() || "";
    
    // If empty, clear it
    if (!pathToSave) {
      try {
        await apiClient.clearDefaultRepository();
        setDefaultRepository(null);
        
        // Refresh insights to ensure all new insights and samples are loaded
        const refreshResult = await apiClient.refreshInsights();
        
        toast({
          title: "Success",
          description: `Cleared default repository. Found ${refreshResult.insights_count} total insights.`,
        });
        // Dispatch event to refresh insights in InsightList
        window.dispatchEvent(new CustomEvent('insights-refreshed'));
      } catch (error) {
        logger.error("Failed to clear default repository:", error);
        toast({
          title: "Error",
          description: String(error),
          variant: "destructive",
        });
      }
      return;
    }

    try {
      await apiClient.setDefaultRepository(pathToSave);
      setDefaultRepository(pathToSave);
      
      // Refresh insights to ensure all new insights and samples are loaded
      const refreshResult = await apiClient.refreshInsights();
      
      toast({
        title: "Success",
        description: `Saved default repository: ${pathToSave}. Found ${refreshResult.insights_count} total insights.`,
      });
      // Dispatch event to refresh insights in InsightList
      window.dispatchEvent(new CustomEvent('insights-refreshed'));
    } catch (error) {
      logger.error("Failed to save default repository:", error);
      toast({
        title: "Error",
        description: String(error),
        variant: "destructive",
      });
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
      // Use unified app-config API
      await apiClient.updateAppConfig({ log_level: newLevel });
      setBackendLogLevel(newLevel);
      // Cache automatically updated by apiClient.updateAppConfig()
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

  const handleHTTPLoggingChange = async (enabled: boolean) => {
    try {
      // Use unified app-config API
      await apiClient.updateAppConfig({ http_logging: enabled });
      setHttpLogging(enabled);
      // Cache automatically updated by apiClient.updateAppConfig()
      toast({
        title: "Success",
        description: `HTTP logging ${enabled ? "enabled" : "disabled"}`,
      });
    } catch (error) {
      logger.error("Failed to update HTTP logging:", error);
      toast({
        title: "Error",
        description: "Failed to update HTTP logging",
        variant: "destructive",
      });
    }
  };

  const handleAIDetailedLoggingChange = async (enabled: boolean) => {
    try {
      // Update via unified app-config API
      await apiClient.updateAppConfig({ detailed_logging: enabled });
      setAiDetailedLogging(enabled);
      // Cache automatically updated by apiClient.updateAppConfig()
      toast({
        title: "Success",
        description: `AI detailed logging ${enabled ? "enabled" : "disabled"}`,
      });
    } catch (error) {
      logger.error("Failed to update AI detailed logging:", error);
      toast({
        title: "Error",
        description: "Failed to update AI detailed logging",
        variant: "destructive",
      });
    }
  };

  const handleAIStreamingChange = async (enabled: boolean) => {
    if (!configName) {
      toast({
        title: "Error",
        description: "No config selected",
        variant: "destructive",
      });
      return;
    }
    
    try {
      await apiClient.updateAIConfig({ streaming_enabled: enabled }, configName);
      setAiStreamingEnabled(enabled);
      toast({
        title: "Success",
        description: `AI streaming ${enabled ? "enabled" : "disabled"}`,
      });
    } catch (error) {
      logger.error("Failed to update AI streaming:", error);
      toast({
        title: "Error",
        description: "Failed to update AI streaming",
        variant: "destructive",
      });
    }
  };

  const handleAIProcessingEnabledChange = async (enabled: boolean) => {
    try {
      // Use unified app-config API
      await apiClient.updateAppConfig({ ai_processing_enabled: enabled });
      setAiProcessingEnabled(enabled);
      // Cache automatically updated by apiClient.updateAppConfig()
      toast({
        title: t("settings.saved"),
        description: `AI processing ${enabled ? "enabled" : "disabled"}`,
      });
    } catch (error) {
      logger.error("Failed to update AI processing enabled:", error);
      toast({
        title: t("common.error"),
        description: `Failed to update AI processing enabled: ${String(error)}`,
        variant: "destructive",
      });
    }
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
      setModelsSource('proxy');
      
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
        
        toast({
          title: "Models Refreshed",
          description: `Loaded ${result.models.length} models`,
        });
      } else {
        toast({
          title: "No Models",
          description: "No models available from the server",
          variant: "destructive",
        });
      }
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
    <div className="flex min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5 font-sans">
      <main className="flex min-h-screen w-full max-w-[90%] flex-col gap-6 pb-8 px-4 mx-auto bg-background/80 backdrop-blur-sm border-x border-border">
        {/* Content */}
        <div className="space-y-6">
          <Tabs defaultValue="ai" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="ai">{t("settings.ai")}</TabsTrigger>
              <TabsTrigger value="insights">{t("settings.insights")}</TabsTrigger>
              <TabsTrigger value="logging">Logging</TabsTrigger>
              <TabsTrigger value="general">{t("settings.general")}</TabsTrigger>
            </TabsList>

            <TabsContent value="ai" className="space-y-4 mt-4">
              {/* Global AI Processing Enabled Toggle */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="ai-processing-enabled">{t("settings.aiEnabled")}</Label>
                  <p className="text-sm text-muted-foreground">
                    {t("settings.aiEnabledHint")}
                  </p>
                </div>
                <Switch
                  id="ai-processing-enabled"
                  checked={aiProcessingEnabled}
                  onCheckedChange={handleAIProcessingEnabledChange}
                />
              </div>

              {/* Config Name Dropdown */}
              <div className="space-y-2">
                <Label htmlFor="config-name">Active Configuration</Label>
                <Select
                  value={configName || undefined}
                  onValueChange={async (value) => {
                    if (value !== configName) {
                      try {
                        setIsLoadingConfigs(true);
                        await apiClient.activateAIConfig(value);
                        setConfigName(value);
                        
                        // Reload settings for the new active config
                        const allConfigs = await apiClient.getAllAIConfigs();
                        const activeConfig = allConfigs.configs[value];
                        if (activeConfig) {
                          // Note: enabled removed - use global aiProcessingEnabled state instead
                          // Honor backend values exactly - no defaults
                          const newSettings = {
                            baseUrl: activeConfig.base_url ?? "",
                            apiKey: activeConfig.api_key ?? "",
                            model: activeConfig.model ?? "",
                            maxTokens: activeConfig.max_tokens ?? 0,
                            temperature: activeConfig.temperature ?? 0,
                          };
                          setSettings(newSettings);
                          setAiStreamingEnabled(activeConfig.streaming_enabled ?? true);
                          // Save to in-memory cache
                          saveAISettings(newSettings);
                        }
                        
                        toast({
                          title: t("settings.saved"),
                          description: `Switched to config '${value}'`,
                        });
                      } catch (error) {
                        logger.error("Failed to activate config:", error);
                        toast({
                          title: t("common.error"),
                          description: `Failed to switch config: ${String(error)}`,
                          variant: "destructive",
                        });
                      } finally {
                        setIsLoadingConfigs(false);
                      }
                    }
                  }}
                  disabled={isLoadingConfigs || allConfigNames.length === 0}
                >
                  <SelectTrigger id="config-name">
                    <SelectValue placeholder={allConfigNames.length === 0 ? "No configs available" : "Select config"} />
                  </SelectTrigger>
                  <SelectContent>
                    {allConfigNames.map((name) => (
                      <SelectItem key={name} value={name}>
                        {name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {allConfigNames.length === 0 
                    ? "No AI configurations available. Create one by saving settings."
                    : "Select which AI configuration profile to use"}
                </p>
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
                  disabled={!aiProcessingEnabled}
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
                  type="text"
                  value={settings.apiKey}
                  onChange={(e) =>
                    setSettings({ ...settings, apiKey: e.target.value })
                  }
                  placeholder="sk-..."
                  disabled={!aiProcessingEnabled}
                />
                <p className="text-xs text-muted-foreground">
                  {t("settings.apiKeyHint")}
                </p>
              </div>

              {/* Model from Config */}
              <div className="space-y-2">
                <Label htmlFor="config-model">Model</Label>
                <Input
                  id="config-model"
                  value={settings.model}
                  readOnly
                  disabled={!aiProcessingEnabled}
                  className="bg-muted"
                />
                <p className="text-xs text-muted-foreground">
                  Current model from configuration
                </p>
              </div>

              {/* Available Models Selection */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="available-models">Available Models</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleRefreshModels}
                    disabled={!aiProcessingEnabled || isLoadingModels || !settings.baseUrl}
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
                  value={availableModels.length > 0 ? settings.model : undefined}
                  onValueChange={(value) =>
                    setSettings({ ...settings, model: value })
                  }
                  disabled={!aiProcessingEnabled || isLoadingModels || availableModels.length === 0}
                >
                  <SelectTrigger id="available-models">
                    <SelectValue placeholder={availableModels.length === 0 ? "Click refresh to load models" : "Select model"} />
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
                    {modelsSource === 'proxy' && availableModels.length > 0 && `✓ ${availableModels.length} models loaded`}
                    {modelsSource === 'error' && `⚠ Failed to load models (server unreachable)`}
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
                  disabled={!aiProcessingEnabled}
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
                  disabled={!aiProcessingEnabled}
                />
                <p className="text-xs text-muted-foreground">
                  {t("settings.temperatureHint")}
                </p>
              </div>

              {/* AI Streaming Toggle */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="ai-streaming">AI Streaming</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable streaming responses from AI service. Disable if your AI server does not support streaming.
                  </p>
                </div>
                <Switch
                  id="ai-streaming"
                  checked={aiStreamingEnabled}
                  onCheckedChange={handleAIStreamingChange}
                  disabled={!aiProcessingEnabled || isLoadingLogging}
                />
              </div>

              {/* Test Connection */}
              <div className="space-y-2">
                <Button
                  variant="outline"
                  onClick={handleTest}
                  disabled={!aiProcessingEnabled || !settings.apiKey || testStatus === "testing"}
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

              {/* Config Action Buttons */}
              <div className="flex gap-2 pt-4 border-t">
                <Button
                  onClick={handleUpdate}
                  disabled={isUpdating || !configName}
                  variant="default"
                  className="flex-1"
                >
                  {isUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Update
                </Button>
                <Button
                  onClick={() => setShowSaveAsDialog(true)}
                  disabled={!configName}
                  variant="outline"
                  className="flex-1"
                >
                  Save As
                </Button>
                <Button
                  onClick={handleDelete}
                  disabled={isDeleting || !configName || allConfigNames.length === 0}
                  variant="destructive"
                  className="flex-1"
                >
                  {isDeleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Delete
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="insights" className="space-y-4 mt-4">
              {/* Default Insights Repository */}
              <div className="space-y-2">
                <Label>Default Insights Repository</Label>
                <p className="text-sm text-muted-foreground">
                  Where new insights will be created when needed. Can be set via .env file (DEFAULT_INSIGHTS_REPOSITORY) as a default, or configured here (this setting takes precedence).
                </p>
                
                {isLoadingDefaultRepo ? (
                  <div className="flex items-center justify-center py-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter path to default repository"
                      value={defaultRepository || ""}
                      onChange={(e) => setDefaultRepository(e.target.value || null)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleSaveDefaultRepository();
                        }
                      }}
                      className="font-mono"
                    />
                    <Button
                      onClick={handleSaveDefaultRepository}
                      className="font-bold"
                    >
                      Save
                    </Button>
                  </div>
                )}
              </div>

              <div className="space-y-2 mt-6 pt-6 border-t">
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

                    {/* HTTP Logging Toggle */}
                    <div className="flex items-center justify-between pt-4 border-t">
                      <div className="space-y-0.5">
                        <Label htmlFor="http-logging">HTTP Request/Response Logging</Label>
                        <p className="text-sm text-muted-foreground">
                          Log all HTTP requests and responses processed by the backend. Useful for debugging API interactions.
                        </p>
                      </div>
                      <Switch
                        id="http-logging"
                        checked={httpLogging}
                        onCheckedChange={handleHTTPLoggingChange}
                        disabled={isLoadingLogging}
                      />
                    </div>

                    {/* AI Detailed Logging Toggle */}
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label htmlFor="ai-detailed-logging">AI Detailed Logging</Label>
                        <p className="text-sm text-muted-foreground">
                          Log detailed AI interaction information including full HTTP requests/responses to AI services.
                        </p>
                      </div>
                      <Switch
                        id="ai-detailed-logging"
                        checked={aiDetailedLogging}
                        onCheckedChange={handleAIDetailedLoggingChange}
                        disabled={isLoadingLogging}
                      />
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

                {/* Result Max Lines */}
                <div className="space-y-2 mt-6 pt-6 border-t">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    <Label htmlFor="result-max-lines">Result Max Lines</Label>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Maximum number of lines to display in result windows. Limits both result display and AI analysis input.
                  </p>
                  {isLoadingResultMaxLines ? (
                    <div className="flex items-center justify-center py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <Input
                        id="result-max-lines"
                        type="number"
                        min="1"
                        max="100000"
                        value={resultMaxLines}
                        onChange={(e) => {
                          const value = parseInt(e.target.value, 10);
                          if (!isNaN(value) && value >= 1 && value <= 100000) {
                            setResultMaxLines(value);
                          }
                        }}
                        onBlur={async () => {
                          // Save on blur
                          try {
                            saveResultMaxLines(resultMaxLines);
                            // Use unified app-config API
                            await apiClient.updateAppConfig({ result_max_lines: resultMaxLines });
                            // Cache automatically updated by apiClient.updateAppConfig()
                            toast({
                              title: "Success",
                              description: `Result max lines updated to ${resultMaxLines}`,
                            });
                          } catch (error) {
                            logger.error("Failed to save result max lines:", error);
                            toast({
                              title: "Error",
                              description: "Failed to save result max lines",
                              variant: "destructive",
                            });
                          }
                        }}
                        className="font-mono"
                      />
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Current value: {resultMaxLines} lines. Changes take effect immediately for new analyses.
                  </p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Save As Dialog */}
        <Dialog open={showSaveAsDialog} onOpenChange={setShowSaveAsDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Save Configuration As</DialogTitle>
              <DialogDescription>
                Enter a name for the new configuration. This will create a copy of the current settings.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="new-config-name">Configuration Name</Label>
                <Input
                  id="new-config-name"
                  value={newConfigName}
                  onChange={(e) => setNewConfigName(e.target.value)}
                  placeholder="Enter config name"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleSaveAs();
                    }
                  }}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowSaveAsDialog(false);
                  setNewConfigName("");
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleSaveAs} disabled={isSavingAs || !newConfigName.trim()}>
                {isSavingAs && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Save
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}
