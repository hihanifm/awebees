/**
 * Centralized logging utility with configurable log levels.
 * Filters console output based on user-configured log level.
 */

import { loadLogLevel, type LogLevel } from "./logging-storage";

// Log level hierarchy (lower number = more verbose)
const LOG_LEVELS: Record<LogLevel, number> = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  NONE: 4,
};

class Logger {
  private currentLevel: LogLevel;

  constructor() {
    this.currentLevel = loadLogLevel();
  }

  /**
   * Update the current log level.
   * @param level New log level
   */
  setLevel(level: LogLevel): void {
    this.currentLevel = level;
  }

  /**
   * Get the current log level.
   * @returns Current log level
   */
  getLevel(): LogLevel {
    return this.currentLevel;
  }

  /**
   * Check if a log level should be output.
   * @param level Log level to check
   * @returns True if should be logged
   */
  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.currentLevel];
  }

  /**
   * Log a debug message.
   * @param args Arguments to log
   */
  debug(...args: any[]): void {
    if (this.shouldLog("DEBUG")) {
      console.log("[DEBUG]", ...args);
    }
  }

  /**
   * Log an info message.
   * @param args Arguments to log
   */
  info(...args: any[]): void {
    if (this.shouldLog("INFO")) {
      console.info("[INFO]", ...args);
    }
  }

  /**
   * Log a warning message.
   * @param args Arguments to log
   */
  warn(...args: any[]): void {
    if (this.shouldLog("WARN")) {
      console.warn("[WARN]", ...args);
    }
  }

  /**
   * Log an error message.
   * @param args Arguments to log
   */
  error(...args: any[]): void {
    if (this.shouldLog("ERROR")) {
      console.error("[ERROR]", ...args);
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Export type for convenience
export type { LogLevel };

