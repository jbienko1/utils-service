import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const target = env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    server: {
      port: 5173,
      proxy: {
        "/v1": { target, changeOrigin: true },
        "/health": { target, changeOrigin: true },
      },
    },
    preview: {
      port: 4173,
      proxy: {
        "/v1": { target, changeOrigin: true },
        "/health": { target, changeOrigin: true },
      },
    },
  };
});
