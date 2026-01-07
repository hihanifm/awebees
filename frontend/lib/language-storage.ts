/**
 * Language preference storage utilities.
 */

export type Language = "en" | "ko";

const STORAGE_KEY = "lens_language";

/**
 * Load language preference from localStorage.
 * @returns The saved language or "en" as default.
 */
export function loadLanguage(): Language {
  if (typeof window === "undefined") {
    return "en";
  }
  
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "en" || saved === "ko") {
    return saved;
  }
  
  return "en";
}

/**
 * Save language preference to localStorage.
 * @param lang The language to save.
 */
export function saveLanguage(lang: Language): void {
  if (typeof window === "undefined") {
    return;
  }
  
  localStorage.setItem(STORAGE_KEY, lang);
}

