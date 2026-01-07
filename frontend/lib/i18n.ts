/**
 * Internationalization utilities for translations.
 */

import { Language, loadLanguage } from "./language-storage";

// Import translation files
import enTranslationsData from "./translations/en.json";
import koTranslationsData from "./translations/ko.json";

type Translations = typeof enTranslationsData;

const translations: Record<Language, Translations> = {
  en: enTranslationsData,
  ko: koTranslationsData,
};

let currentLanguage: Language = "en";

/**
 * Set the current language.
 */
export function setLanguage(lang: Language): void {
  currentLanguage = lang;
}

/**
 * Get the current language.
 */
export function getLanguage(): Language {
  return currentLanguage;
}

/**
 * Initialize language from localStorage.
 */
export function initLanguage(): Language {
  const lang = loadLanguage();
  setLanguage(lang);
  return lang;
}

/**
 * Get translation for a key path.
 * Supports nested keys like "common.save" or "playground.title".
 * @param key The translation key path (e.g., "common.save")
 * @param params Optional parameters for string interpolation
 * @returns The translated string or the key if not found
 */
export function t(key: string, params?: Record<string, string | number>): string {
  const keys = key.split(".");
  let value: any = translations[currentLanguage];
  
  for (const k of keys) {
    if (value && typeof value === "object" && k in value) {
      value = value[k];
    } else {
      // Fallback to English if translation not found
      value = translations.en;
      for (const fallbackKey of keys) {
        if (value && typeof value === "object" && fallbackKey in value) {
          value = value[fallbackKey];
        } else {
          return key; // Return key if not found even in English
        }
      }
      break;
    }
  }
  
  if (typeof value !== "string") {
    return key;
  }
  
  // Simple parameter substitution: {{paramName}}
  if (params) {
    return value.replace(/\{\{(\w+)\}\}/g, (match, paramName) => {
      return params[paramName]?.toString() || match;
    });
  }
  
  return value;
}

/**
 * React hook for translations in components.
 */
import { useState, useEffect, useCallback } from "react";

export function useTranslation() {
  const [language, setLanguageState] = useState<Language>(() => {
    if (typeof window !== "undefined") {
      const lang = loadLanguage();
      setLanguage(lang);
      return lang;
    }
    return "en";
  });

  useEffect(() => {
    const lang = loadLanguage();
    setLanguage(lang);
    setLanguageState(lang);

    // Listen for language changes
    const handleLanguageChange = () => {
      const newLang = loadLanguage();
      setLanguage(newLang);
      setLanguageState(newLang);
    };

    window.addEventListener("languagechange", handleLanguageChange);
    return () => {
      window.removeEventListener("languagechange", handleLanguageChange);
    };
  }, []);

  const changeLanguage = useCallback((lang: Language) => {
    setLanguage(lang);
    setLanguageState(lang);
    // Trigger re-render by dispatching event
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("languagechange"));
    }
  }, []);

  return {
    t,
    language,
    setLanguage: changeLanguage,
  };
}

