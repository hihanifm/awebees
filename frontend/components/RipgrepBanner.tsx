"use client";

import { X, Zap, ExternalLink, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

interface RipgrepBannerProps {
  onDismiss: () => void;
  available: boolean;
}

export function RipgrepBanner({ onDismiss, available }: RipgrepBannerProps) {
  const { t } = useTranslation();

  const getInstallCommand = () => {
    if (typeof window === "undefined") return "";
    
    // More robust OS detection using multiple methods
    const platform = navigator.platform.toLowerCase();
    const userAgent = navigator.userAgent.toLowerCase();
    
    // Windows detection (more comprehensive)
    if (platform.includes("win") || userAgent.includes("windows")) {
      return "winget install BurntSushi.ripgrep.MSVC";
    }
    
    // macOS detection
    if (platform.includes("mac") || userAgent.includes("macintosh") || userAgent.includes("mac os")) {
      return "brew install ripgrep";
    }
    
    // Linux detection
    if (platform.includes("linux") || userAgent.includes("linux")) {
      // Try to detect if it's apt-based (Debian/Ubuntu) or dnf-based (Fedora)
      // Default to apt since it's more common
      return "sudo apt install ripgrep";
    }
    
    return "Check installation instructions for your platform";
  };

  const getInstallCommandsForAllPlatforms = () => {
    return {
      windows: "winget install BurntSushi.ripgrep.MSVC",
      macos: "brew install ripgrep",
      linux: "sudo apt install ripgrep",
      linuxFedora: "sudo dnf install ripgrep"
    };
  };

  const detectOS = () => {
    if (typeof window === "undefined") return "unknown";
    
    const platform = navigator.platform.toLowerCase();
    const userAgent = navigator.userAgent.toLowerCase();
    
    if (platform.includes("win") || userAgent.includes("windows")) {
      return "windows";
    } else if (platform.includes("mac") || userAgent.includes("macintosh") || userAgent.includes("mac os")) {
      return "macos";
    } else if (platform.includes("linux") || userAgent.includes("linux")) {
      return "linux";
    }
    return "unknown";
  };

  const getInstallLink = () => {
    return "https://github.com/BurntSushi/ripgrep#installation";
  };

  if (available) {
    // Positive/celebratory styling when ripgrep is installed
    return (
      <div
        className={cn(
          "rounded-lg border border-green-400 bg-green-50 dark:bg-green-950 dark:border-green-800 px-4 py-3 flex items-start gap-3 shadow-sm"
        )}
      >
        <div className="mt-0.5">
          <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm text-green-700 dark:text-green-300">
            {t("ripgrepBanner.installedTitle")}
          </div>
          <div className="text-xs mt-1 text-green-700 dark:text-green-300">
            {t("ripgrepBanner.installedDescription")}
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 hover:bg-green-200/50 dark:hover:bg-green-800/50"
          onClick={onDismiss}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  // Warning/installation nudge when ripgrep is not installed
  return (
    <div
      className={cn(
        "rounded-lg border border-amber-400 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 px-4 py-3 flex items-start gap-3 shadow-sm"
      )}
    >
      <div className="mt-0.5">
        <Zap className="h-5 w-5 text-amber-600 dark:text-amber-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-sm text-amber-700 dark:text-amber-300">
          {t("ripgrepBanner.title")}
        </div>
        <div className="text-xs mt-1 text-amber-700 dark:text-amber-300">
          {t("ripgrepBanner.description")}
        </div>
        <div className="mt-3 flex flex-wrap gap-2 items-center">
          <div className="font-mono text-xs bg-amber-100 dark:bg-amber-900 px-2 py-1 rounded border border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-200">
            {getInstallCommand()}
          </div>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs border-amber-400 text-amber-700 hover:bg-amber-100 dark:border-amber-600 dark:text-amber-300 dark:hover:bg-amber-900"
            onClick={() => window.open(getInstallLink(), "_blank")}
          >
            <ExternalLink className="h-3 w-3 mr-1" />
            {t("ripgrepBanner.installationGuide")}
          </Button>
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0 hover:bg-amber-200/50 dark:hover:bg-amber-800/50"
        onClick={onDismiss}
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}
