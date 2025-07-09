// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

const site = "https://docs.secgemini.google";

// https://astro.build/config
export default defineConfig({
  site,
  integrations: [
    starlight({
      title: "Sec-Gemini SDK Docs",
      customCss: ["./src/styles/globals.css"],
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
          items: [
            { label: "Getting Started", 
              items: [{"label": "Prerequisites", slug: "guides/getting-started"},
                {"label": "Programmatic Access", slug: "guides/getting-started-sdk"},
                {"label": "Command-line (CLI)", slug: "guides/getting-started-cli"}
              ]
            },
            { label: "Vanilla JS Example", slug: "guides/vanilla" },
            { label: "Webcomponent Example", slug: "guides/webcomponent" },
          ],
        },
        {
          label: "Reference",
          autogenerate: { directory: "reference" },
        },
      ],
      head: [
        {
          tag: "meta",
          attrs: {
            property: "og:image",
            content: site + "/sec-gemini-banner-v2-black.png",
          },
        },
        {
          tag: "meta",
          attrs: {
            property: "twitter:image",
            content: site + "/sec-gemini-banner-v2-black.png",
          },
        },
      ],
    }),
  ],
});
