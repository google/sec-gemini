import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import path from "path";
import { watchAndRun } from "vite-plugin-watch-and-run";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  build: {
    lib: {
      name: "secchat",
      entry: "src/main.js",
      fileName: "swc",
      formats: ["iife"],
    },
  },
  plugins: [
    tailwindcss(),
    svelte(),
    watchAndRun([
      {
        name: "gen",
        watchKind: ["add", "change", "unlink"],
        watch: path.resolve("src/**/*.(gql|svelte)"),
        run: "npm run dev",
      },
    ]),
  ],
});
