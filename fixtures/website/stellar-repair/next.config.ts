import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: { remotePatterns: [] },
  // Use the compiler API from the locked TypeScript 5.x dependency. This
  // avoids an environment-sensitive subprocess path during CI builds.
  experimental: { useTypeScriptCli: false },
};

export default nextConfig;
