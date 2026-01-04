"use client";

import { useState, useCallback } from "react";

export interface SelectedFile {
  file: File;
  path: string;
}

export function useFileSelector() {
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files) return;

    setError(null);
    const newFiles: SelectedFile[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Basic validation
      if (file.size > 100 * 1024 * 1024) { // 100MB limit
        setError(`File ${file.name} is too large (max 100MB)`);
        continue;
      }

      newFiles.push({
        file,
        path: file.name, // In browser, we only have the file name
      });
    }

    setSelectedFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clearFiles = useCallback(() => {
    setSelectedFiles([]);
    setError(null);
  }, []);

  const getFilePaths = useCallback((): string[] => {
    // For browser file selection, we return the file names
    // The backend will need to handle actual file paths differently
    // For now, this is a placeholder - file selection will need to upload files
    return selectedFiles.map((f) => f.path);
  }, [selectedFiles]);

  return {
    selectedFiles,
    error,
    handleFileSelect,
    removeFile,
    clearFiles,
    getFilePaths,
  };
}

