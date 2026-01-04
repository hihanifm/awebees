"use client";

import { useEffect, useState } from "react";
import { Code, Server, Info, CheckCircle2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface VersionResponse {
  version: string;
}

// Get API URL from environment variable
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:34001";

// Get mode from environment (Next.js exposes this at build time)
const MODE = process.env.NODE_ENV === "production" ? "PROD" : "DEV";

export function StatusBar() {
  const [version, setVersion] = useState<string>("...");
  const [versionLoading, setVersionLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking");

  // Fetch version from API
  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await fetch(`${API_URL}/api/version`);
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

    fetchVersion();
    
    // Check API status periodically (every 30 seconds)
    const interval = setInterval(() => {
      fetch(`${API_URL}/api/health`)
        .then((res) => {
          setApiStatus(res.ok ? "online" : "offline");
        })
        .catch(() => {
          setApiStatus("offline");
        });
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
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
                  : "text-amber-600 dark:text-amber-400"
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
                <span className="text-green-600 dark:text-green-400">API Online</span>
              </>
            ) : apiStatus === "offline" ? (
              <>
                <AlertCircle className="h-3.5 w-3.5 text-red-600 dark:text-red-400" />
                <span className="text-red-600 dark:text-red-400">API Offline</span>
              </>
            ) : (
              <>
                <Info className="h-3.5 w-3.5 animate-pulse" />
                <span>Checking...</span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* API URL (truncated if long) */}
          <div className="hidden items-center gap-1.5 md:flex">
            <span className="truncate font-mono text-[10px] max-w-[200px]">
              {API_URL.replace(/^https?:\/\//, "")}
            </span>
          </div>

          {/* Build info */}
          <div className="flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5" />
            <span>Awebees</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

