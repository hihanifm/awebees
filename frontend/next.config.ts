import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',  // Generate static files for serving from FastAPI
  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
  // Fix for multiple lockfiles - set correct workspace root
  experimental: {
    turbo: {
      root: __dirname,
    },
  },
};

export default nextConfig;
