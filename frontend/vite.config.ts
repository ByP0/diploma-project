import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { fileURLToPath, URL } from "node:url";

const resolveSrc = (path: string) => fileURLToPath(new URL(path, import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@app": resolveSrc("./src/app"),
      "@shared": resolveSrc("./src/shared"),
      "@entities": resolveSrc("./src/entities"),
      "@features": resolveSrc("./src/features"),
      "@pages": resolveSrc("./src/pages"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:4000",
        changeOrigin: true,
      },
    },
  },
});
