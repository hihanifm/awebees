"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TextInputPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to main playground with text tab
    router.replace("/playground?tab=text");
  }, [router]);

  return null;
}
