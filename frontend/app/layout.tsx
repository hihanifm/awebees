"use client";

import { useEffect, useState } from "react";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { loadTheme } from "@/lib/theme-storage";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [theme, setTheme] = useState<string>("warm");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Load theme from localStorage on mount
    const savedTheme = loadTheme();
    setTheme(savedTheme);
    setMounted(true);
  }, []);

  useEffect(() => {
    // Apply theme class to html element
    if (mounted && typeof document !== "undefined") {
      const htmlElement = document.documentElement;
      // Remove any existing theme classes
      htmlElement.classList.remove("theme-warm", "theme-purple", "theme-blue", "theme-green");
      // Add the current theme class
      htmlElement.classList.add(`theme-${theme}`);
    }
  }, [theme, mounted]);

  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased pb-10`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
