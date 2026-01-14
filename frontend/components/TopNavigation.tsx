"use client";

import { useState, useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Settings, HelpCircle, Shield } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";
import { apiClient } from "@/lib/api-client";
import { useToast } from "@/components/ui/use-toast";
import { logger } from "@/lib/logger";

interface TopNavigationProps {
  className?: string;
}

export function TopNavigation({ className }: TopNavigationProps) {
  const { t } = useTranslation();
  const pathname = usePathname();
  const [safeMode, setSafeMode] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
  const menuRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLAnchorElement>(null);
  const { toast } = useToast();

  const isActive = (path: string) => pathname === path;

  // Load safe mode state on mount
  useEffect(() => {
    const loadSafeMode = async () => {
      try {
        const state = await apiClient.getSafeMode();
        setSafeMode(state.enabled);
      } catch (error) {
        logger.error("Failed to load safe mode:", error);
      }
    };
    loadSafeMode();
  }, []);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node) &&
          logoRef.current && !logoRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };

    if (menuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [menuOpen]);

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setMenuPosition({ x: e.clientX, y: e.clientY });
    setMenuOpen(true);
  };

  const handleStartSafe = async () => {
    try {
      const result = await apiClient.startSafeMode();
      setSafeMode(result.enabled);
      toast({
        title: "Safe Mode Enabled",
        description: result.message,
      });
      setMenuOpen(false);
      // Dispatch event to update banner
      window.dispatchEvent(new CustomEvent("safe-mode-changed"));
    } catch (error) {
      logger.error("Failed to start safe mode:", error);
      toast({
        title: "Error",
        description: "Failed to enable safe mode",
        variant: "destructive",
      });
    }
  };

  const handleStopSafe = async () => {
    try {
      const result = await apiClient.stopSafeMode();
      setSafeMode(result.enabled);
      toast({
        title: "Safe Mode Disabled",
        description: result.message,
      });
      setMenuOpen(false);
      // Dispatch event to update banner
      window.dispatchEvent(new CustomEvent("safe-mode-changed"));
    } catch (error) {
      logger.error("Failed to stop safe mode:", error);
      toast({
        title: "Error",
        description: "Failed to disable safe mode",
        variant: "destructive",
      });
    }
  };

  return (
    <>
      <nav
        className={cn(
          "fixed top-0 left-0 right-0 z-50 h-16 border-b border-border",
          "bg-gradient-to-r from-primary/5 via-background to-accent/5",
          "backdrop-blur supports-[backdrop-filter]:bg-background/95",
          "shadow-sm",
          className
        )}
      >
        <div className="mx-auto flex h-full w-full items-center px-6 relative">
          {/* App Name */}
          <div className="relative">
            <Link 
              href="/" 
              ref={logoRef}
              className="flex items-center gap-3 no-underline hover:opacity-80 transition-opacity"
              onContextMenu={handleContextMenu}
            >
              <div className="flex flex-col">
                <span className="text-xl font-bold bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent leading-tight">
                  Lens.AI
                </span>
                <span className="text-xs text-muted-foreground leading-tight italic">
                  {t("app.tagline")}
                </span>
              </div>
            </Link>
            
            {/* Context Menu */}
            {menuOpen && (
              <div
                ref={menuRef}
                className="fixed z-50 min-w-[180px] rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
                style={{
                  left: `${menuPosition.x}px`,
                  top: `${menuPosition.y}px`,
                }}
              >
                {safeMode ? (
                  <button
                    onClick={handleStopSafe}
                    className="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                  >
                    <Shield className="mr-2 h-4 w-4" />
                    Stop
                  </button>
                ) : (
                  <button
                    onClick={handleStartSafe}
                    className="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                  >
                    <Shield className="mr-2 h-4 w-4" />
                    Start Safe
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Navigation Tabs - Centered */}
          <div className="absolute left-1/2 transform -translate-x-1/2 flex items-center gap-1">
            {/* Home Tab */}
            <Link
              href="/"
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-all no-underline",
                "hover:bg-primary/10",
                isActive("/")
                  ? "bg-primary/15 text-primary font-semibold border-b-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {t("app.home")}
            </Link>

            {/* Playground Tab */}
            <Link
              href="/playground"
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-all no-underline",
                "hover:bg-primary/10",
                isActive("/playground")
                  ? "bg-primary/15 text-primary font-semibold border-b-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {t("playground.title")}
            </Link>
          </div>

          {/* Help and Settings Tabs - Right */}
          <div className="ml-auto flex items-center gap-1">
            {/* Help Tab */}
            <Link
              href="/help"
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-all no-underline flex items-center gap-2",
                "hover:bg-primary/10",
                isActive("/help")
                  ? "bg-primary/15 text-primary font-semibold border-b-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <HelpCircle className="h-4 w-4" />
              {t("app.help") || "Help"}
            </Link>

            {/* Settings Tab */}
            <Link
              href="/settings"
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-all no-underline flex items-center gap-2",
                "hover:bg-primary/10",
                isActive("/settings")
                  ? "bg-primary/15 text-primary font-semibold border-b-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Settings className="h-4 w-4" />
              {t("common.settings")}
            </Link>
          </div>
        </div>
      </nav>
    </>
  );
}
