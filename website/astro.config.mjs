// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'Sec-Gemini',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/google/sec-gemini' }],
			sidebar: [
				{
					label: 'Introduction',
					items: [
						{ label: 'Overview', link: '/docs/overview/' },
						{ label: 'Installation & Quick Start', link: '/docs/installation-and-quick-start/' },
					],
				},
				{
					label: 'Documentation',
					items: [
						{ label: 'Textual User Interface (TUI)', link: '/docs/tui/' },
						{ label: 'Python SDK', link: '/docs/python-sdk/' },
						{ label: 'Bring Your Own Tools (BYOT)', link: '/docs/byot/' },
					],
				},
				{
					label: 'Demos',
					items: [
						{ label: 'Colabs', link: '/docs/colabs/' },
					],
				},
			],
		}),
	],
  redirects: {
    "/": "/docs/overview/",
    "/docs/": "/docs/overview/",
  },
});
