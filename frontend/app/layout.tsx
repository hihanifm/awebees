"use client";

import { useEffect, useState } from "react";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { TopNavigation } from "@/components/TopNavigation";
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

  // Prevent scroll lock from causing page jumps
  useEffect(() => {
    if (typeof document === "undefined") return;

    const body = document.body;
    let savedScrollY = 0;
    let isLocked = false;
    let originalScrollTo: typeof window.scrollTo;
    let originalScrollIntoView: typeof Element.prototype.scrollIntoView;

    // Continuously track scroll position when NOT locked
    const trackScroll = () => {
      if (!isLocked) {
        savedScrollY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
      }
    };

    // Override window.scrollTo to prevent unwanted scrolls when locked
    originalScrollTo = window.scrollTo;
    const patchedScrollTo = function(this: Window, options?: ScrollToOptions | number, y?: number) {
      if (isLocked) {
        if (typeof options === 'object' && options?.top !== undefined) {
          // If trying to scroll to a different position while locked, use saved position
          if (Math.abs(options.top - savedScrollY) > 5) {
            return originalScrollTo.call(this, { top: savedScrollY, left: 0, behavior: 'auto' });
          }
        } else if (typeof options === 'number') {
          // If trying to scroll to a number while locked, use saved position
          if (Math.abs(options - savedScrollY) > 5) {
            return originalScrollTo.call(this, { top: savedScrollY, left: 0, behavior: 'auto' });
          }
        }
      }
      return originalScrollTo.call(this, options as any, y);
    };

    // Override Element.scrollIntoView to prevent unwanted scrolls
    originalScrollIntoView = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function(this: Element, arg?: boolean | ScrollIntoViewOptions) {
      if (isLocked) {
        // Don't allow scrollIntoView when scroll is locked - it causes the jump
        return;
      }
      return originalScrollIntoView.call(this, arg);
    };

    // Intercept setAttribute to catch scroll lock BEFORE it's applied
    const originalSetAttribute = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name: string, value: string) {
      if (name === 'data-scroll-locked' && this === body) {
        // Save scroll position BEFORE the attribute is set
        savedScrollY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
        
        // Set the attribute
        const result = originalSetAttribute.call(this, name, value);
        
        // Immediately override scrollTo and restore position
        isLocked = true;
        window.scrollTo = patchedScrollTo;
        
        // Restore scroll position immediately and repeatedly
        const restoreImmediately = () => {
          const currentScroll = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
          if (Math.abs(currentScroll - savedScrollY) > 1) {
            originalScrollTo.call(window, { top: savedScrollY, left: 0, behavior: 'auto' });
            // Keep restoring until it sticks
            setTimeout(restoreImmediately, 0);
          }
        };
        
        // Start restoring immediately (synchronously if possible)
        restoreImmediately();
        requestAnimationFrame(restoreImmediately);
        setTimeout(restoreImmediately, 0);
        setTimeout(restoreImmediately, 10);
        setTimeout(restoreImmediately, 20);
        setTimeout(restoreImmediately, 50);
        
        return result;
      }
      return originalSetAttribute.call(this, name, value);
    };
    
    // Also intercept removeAttribute to track when lock is removed
    const originalRemoveAttribute = Element.prototype.removeAttribute;
    Element.prototype.removeAttribute = function(name: string) {
      if (name === 'data-scroll-locked' && this === body) {
        isLocked = false;
        window.scrollTo = originalScrollTo;
      }
      return originalRemoveAttribute.call(this, name);
    };

    // Watch for scroll lock attribute changes as backup
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === "attributes" && mutation.attributeName === "data-scroll-locked") {
          if (body.hasAttribute("data-scroll-locked") && !isLocked) {
            // Backup: save scroll position if we missed it
            savedScrollY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
            isLocked = true;
            window.scrollTo = patchedScrollTo;
          } else if (!body.hasAttribute("data-scroll-locked") && isLocked) {
            isLocked = false;
            window.scrollTo = originalScrollTo;
          }
          
          // Always restore scroll position when locked
          if (isLocked) {
            requestAnimationFrame(() => {
              const currentScroll = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
              if (Math.abs(currentScroll - savedScrollY) > 1) {
                originalScrollTo.call(window, { top: savedScrollY, left: 0, behavior: 'auto' });
              }
            });
          }
        }
      });
    });

    // Continuously track scroll position
    const scrollInterval = setInterval(trackScroll, 16); // ~60fps

    observer.observe(body, {
      attributes: true,
      attributeFilter: ["data-scroll-locked"],
    });

    return () => {
      observer.disconnect();
      clearInterval(scrollInterval);
      // Restore original methods
      if (window.scrollTo !== originalScrollTo) {
        window.scrollTo = originalScrollTo;
      }
      Element.prototype.scrollIntoView = originalScrollIntoView;
      Element.prototype.setAttribute = originalSetAttribute;
      Element.prototype.removeAttribute = originalRemoveAttribute;
    };
  }, []);

  return (
    <html lang={language}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                let savedScrollY = 0;
                let isLocked = false;
                const originalScrollTo = window.scrollTo;
                
                // Continuously track scroll position
                setInterval(function() {
                  if (!isLocked) {
                    savedScrollY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
                  }
                }, 10);
                
                // Intercept setAttribute to catch scroll lock
                const originalSetAttribute = Element.prototype.setAttribute;
                Element.prototype.setAttribute = function(name, value) {
                  if (name === 'data-scroll-locked' && this === document.body) {
                    savedScrollY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
                    isLocked = true;
                    const result = originalSetAttribute.call(this, name, value);
                    
                    // Immediately restore scroll position
                    function restore() {
                      const current = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
                      if (Math.abs(current - savedScrollY) > 1) {
                        originalScrollTo.call(window, { top: savedScrollY, left: 0, behavior: 'auto' });
                        setTimeout(restore, 0);
                      }
                    }
                    restore();
                    requestAnimationFrame(restore);
                    setTimeout(restore, 0);
                    setTimeout(restore, 10);
                    setTimeout(restore, 20);
                    setTimeout(restore, 50);
                    
                    return result;
                  }
                  return originalSetAttribute.call(this, name, value);
                };
                
                // Intercept removeAttribute
                const originalRemoveAttribute = Element.prototype.removeAttribute;
                Element.prototype.removeAttribute = function(name) {
                  if (name === 'data-scroll-locked' && this === document.body) {
                    isLocked = false;
                  }
                  return originalRemoveAttribute.call(this, name);
                };
              })();
            `,
          }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased pb-10 pt-16`}
      >
        <TopNavigation />
        {children}
        <Toaster />
      </body>
    </html>
  );
}
