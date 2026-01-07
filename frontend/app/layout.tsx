"use client";

import { useEffect, useState } from "react";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { loadTheme } from "@/lib/theme-storage";
import { loadLanguage, type Language } from "@/lib/language-storage";
import { initLanguage } from "@/lib/i18n";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin", "latin-ext"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin", "latin-ext"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [theme, setTheme] = useState<string>("warm");
  const [language, setLanguage] = useState<Language>("en");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Load theme and language from localStorage on mount
    const savedTheme = loadTheme();
    const savedLanguage = loadLanguage();
    setTheme(savedTheme);
    setLanguage(savedLanguage);
    initLanguage();
    setMounted(true);

    // Listen for language changes
    const handleLanguageChange = () => {
      const currentLang = loadLanguage();
      setLanguage(currentLang);
      if (typeof document !== "undefined") {
        document.documentElement.lang = currentLang;
      }
    };

    window.addEventListener("languagechange", handleLanguageChange);
    return () => {
      window.removeEventListener("languagechange", handleLanguageChange);
    };
  }, []);

  useEffect(() => {
    // Apply theme class and language to html element
    if (mounted && typeof document !== "undefined") {
      const htmlElement = document.documentElement;
      // Remove any existing theme classes
      htmlElement.classList.remove("theme-warm", "theme-purple", "theme-blue", "theme-green");
      // Add the current theme class
      htmlElement.classList.add(`theme-${theme}`);
      // Set language attribute
      htmlElement.lang = language;
    }
  }, [theme, language, mounted]);

  return (
    <html lang={language}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased pb-10`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
