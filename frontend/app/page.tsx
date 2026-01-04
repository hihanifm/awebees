"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface HelloResponse {
  message: string;
}

// Get API URL from environment variable
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:34001";

export default function Home() {
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const callBackend = async () => {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch(`${API_URL}/api/hello`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: HelloResponse = await response.json();
      setMessage(data.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to call backend");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-center gap-8 py-32 px-16 bg-white dark:bg-black">
        <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
          Awebees Log Analyzer
        </h1>
        
        <div className="flex flex-col items-center gap-4">
          <Button onClick={callBackend} disabled={loading}>
            {loading ? "Calling..." : "Call Backend"}
          </Button>
          
          {message && (
            <div className="rounded-lg border border-black/[.08] bg-zinc-50 px-4 py-3 dark:border-white/[.145] dark:bg-[#1a1a1a]">
              <p className="text-lg text-black dark:text-zinc-50">{message}</p>
            </div>
          )}
          
          {error && (
            <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
              <p className="text-lg text-red-600 dark:text-red-400">Error: {error}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
