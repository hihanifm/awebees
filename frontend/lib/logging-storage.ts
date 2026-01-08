/**
 * Local storage management for logging settings.
 */

export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR" | "NONE";

const STORAGE_KEY = "lens_log_level";

/**
 * Load log level from localStorage.
 * @returns Saved log level or default based on environment
 */
export function loadLogLevel(): LogLevel {
  if (typeof window === "undefined") {
    return "INFO";
  }

  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && isValidLogLevel(saved)) {
      return saved as LogLevel;
    }
  } catch (error) {
    console.error("Failed to load log level from localStorage:", error);
  }

  // Default: INFO in production, DEBUG in development
  return process.env.NODE_ENV === "production" ? "INFO" : "DEBUG";
}

/**
 * Save log level to localStorage.
 * @param level Log level to save
 */
export function saveLogLevel(level: LogLevel): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.setItem(STORAGE_KEY, level);
  } catch (error) {
    console.error("Failed to save log level to localStorage:", error);
  }
}

/**
 * Check if a string is a valid log level.
 * @param level String to check
 * @returns True if valid log level
 */
function isValidLogLevel(level: string): boolean {
  return ["DEBUG", "INFO", "WARN", "ERROR", "NONE"].includes(level);
}

