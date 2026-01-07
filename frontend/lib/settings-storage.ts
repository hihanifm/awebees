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

/**
 * Save AI settings to localStorage.
 */
export function saveAISettings(settings: AISettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch (error) {
    console.error("Failed to save AI settings to localStorage:", error);
  }
}

/**
 * Load AI settings from localStorage.
 */
export function loadAISettings(): AISettings | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    
    return JSON.parse(stored) as AISettings;
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

