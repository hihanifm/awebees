// Theme storage utilities for localStorage

const THEME_STORAGE_KEY = "lens_theme";

export function loadTheme(): string {
  if (typeof window === "undefined") return "warm";
  
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return stored || "warm";
  } catch (error) {
    console.error("Failed to load theme from localStorage:", error);
    return "warm";
  }
}

export function saveTheme(theme: string): void {
  if (typeof window === "undefined") return;
  
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (error) {
    console.error("Failed to save theme to localStorage:", error);
  }
}

