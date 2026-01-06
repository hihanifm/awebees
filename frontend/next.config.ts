import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',  // Generate static files for serving from FastAPI
  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
