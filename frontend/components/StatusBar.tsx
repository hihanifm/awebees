"use client";

import { useEffect, useState } from "react";
import { Code, Server, Info, CheckCircle2, AlertCircle, Activity, FileText, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api-client";
import { useTranslation } from "@/lib/i18n";
import { useToast } from "@/components/ui/use-toast";

interface VersionResponse {
  version: string;
}

// Get API URL from environment variable (use relative path if empty)
const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

// Get mode from environment (Next.js exposes this at build time)
const MODE = process.env.NODE_ENV === "production" ? "PROD" : "DEV";

interface StatusBarProps {
  // No props needed - settings handled by TopNavigation
}

export function StatusBar({}: StatusBarProps) {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [version, setVersion] = useState<string>("...");
  const [versionLoading, setVersionLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking");
  const [profilingEnabled, setProfilingEnabled] = useState<boolean>(false);
  const [ripgrepAvailable, setRipgrepAvailable] = useState<boolean | null>(null);
  const [openingLog, setOpeningLog] = useState<"backend" | "frontend" | null>(null);

  const openLog = async (logType: "backend" | "frontend") => {
    setOpeningLog(logType);
    try {
      const result = await apiClient.openLogFile(logType);
      toast({
        title: "Success",
        description: result.message,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to open log file";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setOpeningLog(null);
    }
  };

  // Fetch version and profiling status from API
  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const url = API_URL ? `${API_URL}/api/version` : "/api/version";
        const response = await fetch(url);
        if (response.ok) {
          const data: VersionResponse = await response.json();
          setVersion(data.version);
          setApiStatus("online");
        } else {
          setVersion("unknown");
          setApiStatus("offline");
        }
      } catch (error) {
        setVersion("unknown");
        setApiStatus("offline");
      } finally {
        setVersionLoading(false);
      }
    };

    const fetchProfilingStatus = async () => {
      try {
        const status = await apiClient.getProfilingStatus();
        setProfilingEnabled(status.enabled);
      } catch (error) {
        // Silently fail - profiling status is not critical
        setProfilingEnabled(false);
      }
    };

    const fetchRipgrepStatus = async () => {
      try {
        const status = await apiClient.checkRipgrepStatus();
        setRipgrepAvailable(status.available);
      } catch (error) {
        // Silently fail - ripgrep status is not critical
        setRipgrepAvailable(null);
      }
    };

    fetchVersion();
    fetchProfilingStatus();
    fetchRipgrepStatus();
    
    // Check API status periodically (every 2 minutes)
    const interval = setInterval(() => {
      fetch(`${API_URL}/api/health`)
        .then((res) => {
          setApiStatus(res.ok ? "online" : "offline");
          // Also refresh profiling status and ripgrep status periodically
          if (res.ok) {
            fetchProfilingStatus();
            fetchRipgrepStatus();
          }
        })
        .catch(() => {
          setApiStatus("offline");
        });
    }, 120000); // 2 minutes (120000 ms)

    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-gradient-to-r from-primary/5 via-background/95 to-accent/5 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-10 max-w-screen-2xl items-center justify-between px-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-4">
          {/* Version */}
          <div className="flex items-center gap-1.5">
            <Code className="h-3.5 w-3.5" />
            <span className="font-mono">v{version}</span>
          </div>

          {/* Mode */}
          <div className="flex items-center gap-1.5">
            <Server className="h-3.5 w-3.5" />
            <span
              className={cn(
                "font-medium",
                MODE === "PROD" 
                  ? "text-green-600 dark:text-green-400" 
                  : "text-accent"
              )}
            >
              {MODE}
            </span>
          </div>

          {/* API Status */}
          <div className="flex items-center gap-1.5">
            {apiStatus === "online" ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
                <span className="text-green-600 dark:text-green-400">{t("statusBar.apiOnline")}</span>
              </>
            ) : apiStatus === "offline" ? (
              <>
                <AlertCircle className="h-3.5 w-3.5 text-red-600 dark:text-red-400" />
                <span className="text-red-600 dark:text-red-400">{t("statusBar.apiOffline")}</span>
              </>
            ) : (
              <>
                <Info className="h-3.5 w-3.5 animate-pulse" />
                <span>{t("statusBar.checking")}</span>
              </>
            )}
          </div>

          {/* Profiling Status */}
          {profilingEnabled && (
            <div className="flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
              <span className="text-purple-600 dark:text-purple-400 font-medium">{t("statusBar.profiling")}</span>
            </div>
          )}

          {/* Ripgrep Status */}
          {ripgrepAvailable !== null && (
            <a
              href="/docs/RIPGREP_GUIDE.md"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 hover:opacity-80 transition-opacity cursor-pointer"
              title="Ripgrep Guide"
            >
              {ripgrepAvailable ? (
                <>
                  <Zap className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
                  <span className="text-green-600 dark:text-green-400">{t("statusBar.ripgrepInstalled")}</span>
                </>
              ) : (
                <>
                  <Zap className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                  <span className="text-amber-600 dark:text-amber-400">{t("statusBar.ripgrepNotInstalled")}</span>
                </>
              )}
            </a>
          )}
        </div>

        <div className="flex items-center gap-4">
          {/* Log viewer buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => openLog("backend")}
              disabled={openingLog !== null}
              className="flex items-center gap-1.5 hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={t("statusBar.backendLog")}
            >
              <FileText className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{t("statusBar.backendLog")}</span>
            </button>
            <button
              onClick={() => openLog("frontend")}
              disabled={openingLog !== null}
              className="flex items-center gap-1.5 hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={t("statusBar.frontendLog")}
            >
              <FileText className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{t("statusBar.frontendLog")}</span>
            </button>
          </div>

          {/* API URL (truncated if long) */}
          <div className="hidden items-center gap-1.5 md:flex">
            <span className="truncate font-mono text-[10px] max-w-[200px]">
              {API_URL.replace(/^https?:\/\//, "")}
            </span>
          </div>

          {/* Build info */}
          <div className="flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5" />
            <span>LensAI</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

