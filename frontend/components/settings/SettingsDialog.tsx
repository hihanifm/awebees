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
import { Settings, Loader2, CheckCircle2, XCircle, FolderOpen, X, RefreshCw, Palette } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { themes } from "@/lib/themes";
import { loadTheme, saveTheme } from "@/lib/theme-storage";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const { toast } = useToast();
  const [settings, setSettings] = useState<AISettings>({
    enabled: false,
    baseUrl: "https://api.openai.com/v1",
    apiKey: "",
    model: "gpt-4o-mini",
    maxTokens: 2000,
    temperature: 0.7,
  });

  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [testMessage, setTestMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Theme state
  const [selectedTheme, setSelectedTheme] = useState<string>("warm");

  // Insight paths state
  const [insightPaths, setInsightPaths] = useState<string[]>([]);
  const [newPath, setNewPath] = useState("");
  const [isLoadingPaths, setIsLoadingPaths] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        // Load from localStorage
        const localSettings = loadAISettings();
        
        // Load from backend
        const backendConfig = await getAIConfig();
        
        // Merge: local overrides backend
        const merged: AISettings = {
          enabled: localSettings?.enabled ?? backendConfig.enabled ?? false,
          baseUrl: localSettings?.baseUrl ?? backendConfig.base_url ?? "https://api.openai.com/v1",
          apiKey: localSettings?.apiKey ?? "",
          model: localSettings?.model ?? backendConfig.model ?? "gpt-4o-mini",
          maxTokens: localSettings?.maxTokens ?? backendConfig.max_tokens ?? 2000,
          temperature: localSettings?.temperature ?? backendConfig.temperature ?? 0.7,
        };
        
        setSettings(merged);
      } catch (error) {
        console.error("Failed to load AI settings:", error);
      }
    };
    
    const loadInsightPaths = async () => {
      setIsLoadingPaths(true);
      try {
        const paths = await apiClient.getInsightPaths();
        setInsightPaths(paths);
      } catch (error) {
        console.error("Failed to load insight paths:", error);
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
    
    if (open) {
      loadSettings();
      loadInsightPaths();
      loadThemeSettings();
    }
  }, [open, toast]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Save to localStorage
      saveAISettings(settings);
      
      // Send to backend
      await updateAIConfig({
        enabled: settings.enabled,
        base_url: settings.baseUrl,
        api_key: settings.apiKey,
        model: settings.model,
        max_tokens: settings.maxTokens,
        temperature: settings.temperature,
      });
      
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to save settings:", error);
      alert("Failed to save settings. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    setTestStatus("testing");
    setTestMessage("Testing connection...");
    
    try {
      const result = await testAIConnection();
      
      if (result.success) {
        setTestStatus("success");
        setTestMessage(result.message);
      } else {
        setTestStatus("error");
        setTestMessage(result.message);
      }
    } catch (error) {
      setTestStatus("error");
      setTestMessage("Connection test failed: " + String(error));
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
      console.error("Failed to add insight path:", error);
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
      console.error("Failed to remove insight path:", error);
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
      console.error("Failed to refresh insights:", error);
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Settings
          </DialogTitle>
          <DialogDescription>
            Configure Lens application settings
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="ai" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="ai">AI Settings</TabsTrigger>
            <TabsTrigger value="insights">External Insights</TabsTrigger>
            <TabsTrigger value="general">General</TabsTrigger>
          </TabsList>

          <TabsContent value="ai" className="space-y-4 mt-4">
            {/* AI Enabled Toggle */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="ai-enabled">Enable AI Processing</Label>
                <p className="text-sm text-muted-foreground">
                  Use AI to analyze insight results
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
              <Label htmlFor="base-url">API Base URL</Label>
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
                OpenAI-compatible API endpoint (e.g., Azure OpenAI, Ollama)
              </p>
            </div>

            {/* API Key */}
            <div className="space-y-2">
              <Label htmlFor="api-key">API Key</Label>
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
                Your OpenAI API key (stored locally)
              </p>
            </div>

            {/* Model Selection */}
            <div className="space-y-2">
              <Label htmlFor="model">Model</Label>
              <Select
                value={settings.model}
                onValueChange={(value) =>
                  setSettings({ ...settings, model: value })
                }
                disabled={!settings.enabled}
              >
                <SelectTrigger id="model">
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                  <SelectItem value="gpt-4o-mini">GPT-4o-mini</SelectItem>
                  <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                  <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Max Tokens */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="max-tokens">Max Tokens</Label>
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
                <Label htmlFor="temperature">Temperature</Label>
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
                Higher values make output more random, lower more deterministic
              </p>
            </div>

            {/* Test Connection */}
            <div className="space-y-2">
              <Button
                variant="outline"
                onClick={handleTest}
                disabled={!settings.enabled || !settings.apiKey || testStatus === "testing"}
                className="w-full"
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
                Test Connection
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
              <Label>External Insight Paths</Label>
              <p className="text-sm text-muted-foreground">
                Add directories containing custom insights. Click Refresh to reload after making changes.
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
                  No external insight paths configured
                </div>
              )}
              
              {/* Add new path */}
              <div className="flex gap-2">
                <Input
                  placeholder="/path/to/insights"
                  value={newPath}
                  onChange={(e) => setNewPath(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleAddPath();
                    }
                  }}
                  className="font-mono"
                />
                <Button onClick={handleAddPath} variant="secondary">
                  Add
                </Button>
              </div>
              
              {/* Refresh button */}
              <Button
                variant="outline"
                onClick={handleRefreshInsights}
                disabled={isRefreshing}
                className="w-full"
              >
                {isRefreshing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Refresh Insights
              </Button>
              <p className="text-xs text-muted-foreground">
                Manually reload all insights from built-in and external paths
              </p>
            </div>
          </TabsContent>

          <TabsContent value="general" className="space-y-4 mt-4">
            <div className="space-y-4">
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
                  Choose your preferred color scheme. Changes apply immediately.
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
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

