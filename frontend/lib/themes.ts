// Theme configuration for Lens application
// Using OKLCH color space for consistent perceptual brightness

export interface ThemeConfig {
  id: string;
  name: string;
  description: string;
  preview: string; // Color for preview circle
}

export const themes: ThemeConfig[] = [
  {
    id: "warm",
    name: "Warm",
    description: "Orange/Coral tones (default)",
    preview: "oklch(0.62 0.15 40)", // Coral
  },
  {
    id: "purple",
    name: "Purple",
    description: "Instagram-inspired purple/magenta",
    preview: "oklch(0.65 0.25 320)", // Purple
  },
  {
    id: "blue",
    name: "Blue",
    description: "Professional blue/cyan tones",
    preview: "oklch(0.60 0.20 240)", // Blue
  },
  {
    id: "green",
    name: "Green",
    description: "Fresh green/teal tones",
    preview: "oklch(0.65 0.22 150)", // Green
  },
];

export const DEFAULT_THEME = "warm";

