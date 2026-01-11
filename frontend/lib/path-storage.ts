/**
 * Local storage management for file path history.
 * Stores the last 15 unique path values with smart deduplication.
 */

const STORAGE_KEY = "lens_path_history";
const MAX_CACHED_PATHS = 15;

/**
 * Save a path to the cache.
 * - Deduplicates: if path exists, moves it to the front
 * - Limits to MAX_CACHED_PATHS items (removes oldest if needed)
 * - Ignores empty paths
 */
export function savePath(path: string): void {
  if (!path || !path.trim()) {
    return; // Don't cache empty paths
  }

  try {
    const trimmedPath = path.trim();
    let cachedPaths = getCachedPaths();

    // Remove the path if it already exists (will be added to front)
    cachedPaths = cachedPaths.filter((p) => p !== trimmedPath);

    // Add to the front (most recent)
    cachedPaths.unshift(trimmedPath);

    // Limit to MAX_CACHED_PATHS
    if (cachedPaths.length > MAX_CACHED_PATHS) {
      cachedPaths = cachedPaths.slice(0, MAX_CACHED_PATHS);
    }

    // Save to localStorage
    const serialized = JSON.stringify(cachedPaths);
    localStorage.setItem(STORAGE_KEY, serialized);
  } catch (error) {
    console.error("Failed to save path to localStorage:", error);
  }
}

/**
 * Get all cached paths (most recent first).
 */
export function getCachedPaths(): string[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return [];
    }
    const parsed = JSON.parse(stored) as string[];
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.error("Failed to load cached paths from localStorage:", error);
    return [];
  }
}

/**
 * Get the most recently used path.
 */
export function getMostRecentPath(): string | null {
  const cachedPaths = getCachedPaths();
  return cachedPaths.length > 0 ? cachedPaths[0] : null;
}

/**
 * Clear all cached paths.
 */
export function clearCachedPaths(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error("Failed to clear cached paths from localStorage:", error);
  }
}
