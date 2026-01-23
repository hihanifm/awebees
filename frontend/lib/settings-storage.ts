/**
 * In-memory cache management for all settings.
 * All settings are cached in memory after being read from the server.
 */

export interface AISettings {
  // Note: enabled removed - use global AppConfig.AI_PROCESSING_ENABLED instead
  baseUrl: string;
  apiKey: string;
  model: string;
  maxTokens: number;
  temperature: number;
}

const RESULT_MAX_LINES_STORAGE_KEY = "lens_result_max_lines";

// In-memory cache for all config.json settings
interface AppConfigCache {
  log_level: string;
  ai_processing_enabled: boolean;
  http_logging: boolean;
  result_max_lines: number;
}

// In-memory cache for AI settings
let aiSettingsCache: { value: AISettings; timestamp: number } | null = null;
let appConfigCache: { value: AppConfigCache; timestamp: number } | null = null;
// In-memory cache for all AI configs (from getAllAIConfigs)
let allAIConfigsCache: { value: { active_config_name: string | null; configs: Record<string, any> }; timestamp: number } | null = null;
const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes cache

/**
 * Save AI settings to in-memory cache.
 * @param settings AI settings to cache
 */
export function saveAISettings(settings: AISettings): void {
  aiSettingsCache = {
    value: settings,
    timestamp: Date.now()
  };
  console.log("[settings-storage] Cached AI settings in memory:", settings);
}

/**
 * Load AI settings from in-memory cache.
 * Returns null if cache is expired or not found.
 * @returns Cached settings or null if cache is invalid/expired
 */
export function loadAISettings(): AISettings | null {
  if (!aiSettingsCache) {
    return null;
  }
  
  // Check if cache is expired
  const cacheAge = Date.now() - aiSettingsCache.timestamp;
  if (cacheAge > CACHE_DURATION_MS) {
    console.log("[settings-storage] AI settings cache expired, clearing");
    aiSettingsCache = null;
    return null;
  }
  
  console.log("[settings-storage] Loaded AI settings from memory cache");
  return aiSettingsCache.value;
}

/**
 * Clear AI settings cache from memory.
 */
export function clearAISettings(): void {
  aiSettingsCache = null;
}

/**
 * Merge local settings with backend defaults.
 * Local settings take precedence over backend defaults.
 */
export function mergeWithDefaults(
  local: AISettings | null,
  backend: Partial<AISettings>
): AISettings {
  // Honor backend values exactly - no hardcoded defaults
  // Note: enabled removed - use global AppConfig.AI_PROCESSING_ENABLED instead
  return {
    baseUrl: local?.baseUrl ?? backend.baseUrl ?? "",
    apiKey: local?.apiKey ?? backend.apiKey ?? "",
    model: local?.model ?? backend.model ?? "",
    maxTokens: local?.maxTokens ?? backend.maxTokens ?? 0,
    temperature: local?.temperature ?? backend.temperature ?? 0,
  };
}

/**
 * Save result max lines setting to in-memory cache (via appConfigCache).
 * This is now part of AppConfigCache, but kept for backward compatibility.
 */
export function saveResultMaxLines(value: number): void {
  // Update appConfigCache if it exists
  if (appConfigCache) {
    appConfigCache.value.result_max_lines = value;
    appConfigCache.timestamp = Date.now();
    console.log("[settings-storage] Updated result max lines in app config cache:", value);
  }
}

/**
 * Load result max lines setting from in-memory cache (via appConfigCache).
 * Returns null if not set, otherwise returns the number.
 */
export function loadResultMaxLines(): number | null {
  const appConfig = loadAppConfig();
  return appConfig?.result_max_lines ?? null;
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

/**
 * Save all AI configs to in-memory cache.
 * @param configs All AI configs from getAllAIConfigs
 */
export function saveAllAIConfigs(configs: { active_config_name: string | null; configs: Record<string, any> }): void {
  allAIConfigsCache = {
    value: configs,
    timestamp: Date.now()
  };
  console.log("[settings-storage] Cached all AI configs in memory");
  
  // Also update aiSettingsCache with the active config
  if (configs.active_config_name && configs.configs[configs.active_config_name]) {
    const activeConfig = configs.configs[configs.active_config_name];
    const aiSettings: AISettings = {
      baseUrl: activeConfig.base_url ?? "",
      apiKey: activeConfig.api_key ?? "",
      model: activeConfig.model ?? "",
      maxTokens: activeConfig.max_tokens ?? 0,
      temperature: activeConfig.temperature ?? 0,
    };
    saveAISettings(aiSettings);
  }
}

/**
 * Load all AI configs from in-memory cache.
 * Returns null if cache is expired or not found.
 * @returns Cached configs or null if cache is invalid/expired
 */
export function loadAllAIConfigs(): { active_config_name: string | null; configs: Record<string, any> } | null {
  if (!allAIConfigsCache) {
    return null;
  }
  
  // Check if cache is expired
  const cacheAge = Date.now() - allAIConfigsCache.timestamp;
  if (cacheAge > CACHE_DURATION_MS) {
    console.log("[settings-storage] All AI configs cache expired, clearing");
    allAIConfigsCache = null;
    return null;
  }
  
  console.log("[settings-storage] Loaded all AI configs from memory cache");
  return allAIConfigsCache.value;
}

/**
 * Clear all AI configs cache from memory.
 */
export function clearAllAIConfigs(): void {
  allAIConfigsCache = null;
}

/**
 * Get all AI configs with cache support.
 * Checks cache first, then calls API if cache is empty/expired.
 * This is a wrapper that should be used instead of direct API calls.
 */
export async function getAllAIConfigsWithCache(
  apiClient: { getAllAIConfigs: () => Promise<{ active_config_name: string | null; configs: Record<string, any> }> }
): Promise<{ active_config_name: string | null; configs: Record<string, any> }> {
  // Check cache first
  let configs = loadAllAIConfigs();
  
  // If cache miss or expired, fetch from API
  if (!configs) {
    configs = await apiClient.getAllAIConfigs();
    saveAllAIConfigs(configs);
  }
  
  return configs;
}

/**
 * Get app config with cache support.
 * Checks cache first, then calls API if cache is empty/expired.
 * This is a wrapper that should be used instead of direct API calls.
 */
export async function getAppConfigWithCache(
  apiClient: { getAppConfig: () => Promise<AppConfigCache> }
): Promise<AppConfigCache> {
  // Check cache first
  let config = loadAppConfig();
  
  // If cache miss or expired, fetch from API
  if (!config) {
    config = await apiClient.getAppConfig();
    saveAppConfig(config);
  }
  
  return config;
}

