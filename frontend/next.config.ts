import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the workspace root explicitly — without this, Next.js/Turbopack can
  // mistakenly infer it from an unrelated lockfile higher up the filesystem
  // (e.g. in the user's home directory), which triggers a spurious warning.
  turbopack: {
    root: path.join(__dirname),
  },
  // Produces a self-contained `.next/standalone` build (its own trimmed
  // node_modules) — needed for a lean production Docker image.
  output: "standalone",
};

export default nextConfig;
