/**
 * Local storage management for input value history.
 * Stores the last 10 unique values with smart deduplication.
 */

const MAX_CACHED_VALUES = 10;

/**
 * Save a value to the cache for a given storage key.
 * - Deduplicates: if value exists, moves it to the front
 * - Limits to MAX_CACHED_VALUES items (removes oldest if needed)
 * - Ignores empty values
 */
export function saveInputHistory(storageKey: string, value: string): void {
  if (!value || !value.trim()) {
    return; // Don't cache empty values
  }

  try {
    const trimmedValue = value.trim();
    let cachedValues = getInputHistory(storageKey);

    // Remove the value if it already exists (will be added to front)
    cachedValues = cachedValues.filter((v) => v !== trimmedValue);

    // Add to the front (most recent)
    cachedValues.unshift(trimmedValue);

    // Limit to MAX_CACHED_VALUES
    if (cachedValues.length > MAX_CACHED_VALUES) {
      cachedValues = cachedValues.slice(0, MAX_CACHED_VALUES);
    }

    // Save to localStorage
    const serialized = JSON.stringify(cachedValues);
    localStorage.setItem(storageKey, serialized);
  } catch (error) {
    console.error(`Failed to save input history to localStorage for key ${storageKey}:`, error);
  }
}

/**
 * Get all cached values for a given storage key (most recent first).
 */
export function getInputHistory(storageKey: string): string[] {
  try {
    const stored = localStorage.getItem(storageKey);
    if (!stored) {
      return [];
    }
    const parsed = JSON.parse(stored) as string[];
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.error(`Failed to load input history from localStorage for key ${storageKey}:`, error);
    return [];
  }
}

/**
 * Get the most recently used value for a given storage key.
 */
export function getMostRecentInput(storageKey: string): string | null {
  const cachedValues = getInputHistory(storageKey);
  return cachedValues.length > 0 ? cachedValues[0] : null;
}

/**
 * Clear all cached values for a given storage key.
 */
export function clearInputHistory(storageKey: string): void {
  try {
    localStorage.removeItem(storageKey);
  } catch (error) {
    console.error(`Failed to clear input history from localStorage for key ${storageKey}:`, error);
  }
}
