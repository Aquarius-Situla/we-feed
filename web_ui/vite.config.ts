import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiTarget = env.VITE_PROXY_TARGET || env.VITE_API_BASE_URL || "http://127.0.0.1:8001/";

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    base: "/",
    build: {
      outDir: "../static",
      emptyOutDir: false,
      assetsDir: "assets",
    },
    server: {
      host: "0.0.0.0",
      port: 3000,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/static": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/feed": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/rss": {
          target: apiTarget,
          changeOrigin: true,
        },
        "/files": {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
