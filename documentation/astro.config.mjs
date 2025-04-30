// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

// https://astro.build/config
export default defineConfig({
  integrations: [
    starlight({
      title: "Sec-Gemini SDK Docs",
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/google/sec-gemini/",
        },
      ],
      sidebar: [
        {
          label: "Guides",
          items: [{ label: "Typescript Example", slug: "guides/typescript" }],
        },
        {
          label: "Reference",
          autogenerate: { directory: "reference" },
        },
      ],
    }),
  ],
});
