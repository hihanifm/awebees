/**
 * Local storage management for AI settings.
 * Settings are stored in browser localStorage and merged with backend defaults.
 */

export interface AISettings {
  enabled: boolean;
  baseUrl: string;
  apiKey: string;
  model: string;
  maxTokens: number;
  temperature: number;
}

const STORAGE_KEY = "lens_ai_settings";
const RESULT_MAX_LINES_STORAGE_KEY = "lens_result_max_lines";

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
    enabled: local?.enabled ?? backend.enabled ?? false,
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

