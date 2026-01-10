"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";
import { SettingsDialog } from "@/components/settings/SettingsDialog";

interface TopNavigationProps {
  className?: string;
}

export function TopNavigation({ className }: TopNavigationProps) {
  const { t } = useTranslation();
  const pathname = usePathname();
  const [settingsOpen, setSettingsOpen] = useState(false);

  const isActive = (path: string) => pathname === path;

  return (
    <>
      <nav
        className={cn(
          "fixed top-0 left-0 right-0 z-50 h-16 border-b border-border",
          "bg-gradient-to-r from-primary/5 via-[oklch(0.96_0.02_50)] to-accent/5",
          "backdrop-blur supports-[backdrop-filter]:bg-[oklch(0.96_0.02_50)]/95",
          "shadow-sm",
          className
        )}
      >
        <div className="mx-auto flex h-full w-full items-center px-6 relative">
          {/* Logo and App Name */}
          <Link href="/" className="flex items-center gap-3 no-underline hover:opacity-80 transition-opacity">
            <img
              src="/lensAI.png"
              alt="LensAI"
              className="h-16 w-auto"
            />
            <div className="flex flex-col">
              <span className="text-xl font-bold bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent leading-tight">
                Lens.AI
              </span>
              <span className="text-xs text-muted-foreground leading-tight italic">
                {t("app.tagline")}
              </span>
            </div>
          </Link>

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

          {/* Settings Tab - Right */}
          <div className="ml-auto flex items-center">
            <button
              onClick={() => setSettingsOpen(true)}
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                "hover:bg-primary/10",
                settingsOpen
                  ? "bg-primary/15 text-primary font-semibold border-b-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Settings className="h-4 w-4" />
              {t("common.settings")}
            </button>
          </div>
        </div>
      </nav>

      {/* Settings Dialog */}
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </>
  );
}
