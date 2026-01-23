/**
 * Local storage management for AI settings.
 * Settings are stored in browser localStorage and merged with backend defaults.
 */

export interface AISettings {
  // Note: enabled removed - use global AppConfig.AI_PROCESSING_ENABLED instead
  baseUrl: string;
  apiKey: string;
  model: string;
  maxTokens: number;
  temperature: number;
}

const STORAGE_KEY = "lens_ai_settings";
const RESULT_MAX_LINES_STORAGE_KEY = "lens_result_max_lines";

// In-memory cache for all config.json settings
interface AppConfigCache {
  log_level: string;
  ai_processing_enabled: boolean;
  http_logging: boolean;
  result_max_lines: number;
}

let appConfigCache: { value: AppConfigCache; timestamp: number } | null = null;
const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes cache

/**
 * Save AI settings to localStorage.
 */
export function saveAISettings(settings: AISettings): void {
  try {
    const serialized = JSON.stringify(settings);
    console.log("[settings-storage] Saving to localStorage:", settings);
    localStorage.setItem(STORAGE_KEY, serialized);
    // Verify it was saved
    const verified = localStorage.getItem(STORAGE_KEY);
    console.log("[settings-storage] Verified saved data:", verified);
  } catch (error) {
    console.error("Failed to save AI settings to localStorage:", error);
    throw error; // Re-throw so caller knows save failed
  }
}

/**
 * Load AI settings from localStorage.
 */
export function loadAISettings(): AISettings | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    console.log("[settings-storage] Raw data from localStorage:", stored);
    if (!stored) {
      console.log("[settings-storage] No settings found in localStorage");
      return null;
    }
    
    const parsed = JSON.parse(stored) as AISettings;
    console.log("[settings-storage] Parsed settings:", parsed);
    return parsed;
  } catch (error) {
    console.error("Failed to load AI settings from localStorage:", error);
    return null;
  }
}

/**
 * Clear AI settings from localStorage.
 */
export function clearAISettings(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error("Failed to clear AI settings from localStorage:", error);
  }
}

/**
 * Merge local settings with backend defaults.
 * Local settings take precedence over backend defaults.
 */
export function mergeWithDefaults(
  local: AISettings | null,
  backend: Partial<AISettings>
): AISettings {
  return {
    // Note: enabled removed - use global AppConfig.AI_PROCESSING_ENABLED instead
    baseUrl: local?.baseUrl ?? backend.baseUrl ?? "https://api.openai.com/v1",
    apiKey: local?.apiKey ?? backend.apiKey ?? "",
    model: local?.model ?? backend.model ?? "gpt-4o-mini",
    maxTokens: local?.maxTokens ?? backend.maxTokens ?? 2000,
    temperature: local?.temperature ?? backend.temperature ?? 0.7,
  };
}

/**
 * Save result max lines setting to localStorage.
 */
export function saveResultMaxLines(value: number): void {
  try {
    localStorage.setItem(RESULT_MAX_LINES_STORAGE_KEY, value.toString());
    console.log("[settings-storage] Saved result max lines:", value);
  } catch (error) {
    console.error("Failed to save result max lines to localStorage:", error);
    throw error;
  }
}

/**
 * Load result max lines setting from localStorage.
 * Returns null if not set, otherwise returns the number.
 */
export function loadResultMaxLines(): number | null {
  try {
    const stored = localStorage.getItem(RESULT_MAX_LINES_STORAGE_KEY);
    if (!stored) {
      return null;
    }
    
    const value = parseInt(stored, 10);
    if (isNaN(value) || value < 1) {
      console.warn("[settings-storage] Invalid result max lines value, removing");
      localStorage.removeItem(RESULT_MAX_LINES_STORAGE_KEY);
      return null;
    }
    
    return value;
  } catch (error) {
    console.error("Failed to load result max lines from localStorage:", error);
    return null;
  }
}

/**
 * Save all app config settings to in-memory cache.
 * @param config All config.json settings
 */
export function saveAppConfig(config: AppConfigCache): void {
  appConfigCache = {
    value: config,
    timestamp: Date.now()
  };
  console.log("[settings-storage] Cached app config in memory:", config);
}

/**
 * Load all app config settings from in-memory cache.
 * Returns null if cache is expired or not found.
 * @returns Cached config or null if cache is invalid/expired
 */
export function loadAppConfig(): AppConfigCache | null {
  if (!appConfigCache) {
    return null;
  }
  
  // Check if cache is expired
  const cacheAge = Date.now() - appConfigCache.timestamp;
  if (cacheAge > CACHE_DURATION_MS) {
    console.log("[settings-storage] App config cache expired, clearing");
    appConfigCache = null;
    return null;
  }
  
  console.log("[settings-storage] Loaded app config from memory cache");
  return appConfigCache.value;
}

/**
 * Clear app config cache from memory.
 */
export function clearAppConfig(): void {
  appConfigCache = null;
}

/**
 * Get a specific setting from cache (convenience method).
 * @param key Setting key to retrieve
 * @returns Cached value or null if cache is invalid/expired
 */
export function getAppConfigValue<K extends keyof AppConfigCache>(key: K): AppConfigCache[K] | null {
  const config = loadAppConfig();
  return config ? config[key] : null;
}

