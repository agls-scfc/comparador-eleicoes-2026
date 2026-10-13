import { defineConfig } from "astro/config";

// SITE_BASE: caminho de publicação (ex.: /comparador-eleicoes-2026/ no GitHub Pages).
export default defineConfig({
  base: process.env.SITE_BASE || "/",
  trailingSlash: "always",
  build: { format: "directory" },
});
