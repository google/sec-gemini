import MarkdownIt from "markdown-it";
import DOMPurify from "dompurify";
import * as Prism from "prismjs";

import "prismjs/themes/prism-tomorrow.css"; // or another theme
import "prismjs/components/prism-python";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-bash";
import "prismjs/components/prism-json";
import "prismjs/components/prism-yaml";
import "prismjs/components/prism-markdown";
import "prismjs/components/prism-docker";

const customPurifyOptions = {
  USE_PROFILES: { html: true }, // Allows common HTML tags
};

class SafeMarkdownIt extends MarkdownIt {
  constructor(options: any) {
    super(options);
  }

  render(src: string, env?: any): string {
    const sanitizedSrc = DOMPurify.sanitize(src, customPurifyOptions);
    return super.render(sanitizedSrc, env);
  }
}

const md: any = new SafeMarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  typographer: true,
  highlight: function (str: string, lang: string) {
    let language = lang || "text";
    let highlighted;

    try {
      if (lang && Prism.languages[lang]) {
        highlighted = Prism.highlight(str, Prism.languages[lang], lang);
      } else {
        highlighted = md.utils.escapeHtml(str);
      }
    } catch (error) {
      highlighted = md.utils.escapeHtml(str);
    }

    return `<div class="flex flex-col overflow-hidden">
        <div class="flex justify-between items-center py-1 px-4 bg-[#2d2d2d] rounded-t-xl">
          <span class="uppercase font-mono font-medium text-sm !ml-0">${language}</span>
          <button
            data-raw-code="${md.utils.escapeHtml(str)}" 
            class="copy-code text-sm transition-colors duration-200 h-8 w-8 rounded-full relative hover:cursor-pointer hover:text-black hover:bg-white">
            <svg class="absolute top-1.5 right-1.5 text-inherit" xmlns="http://www.w3.org/2000/svg" width="1.5em" height="1.5em" viewBox="0 0 24 24" {...props}>
            <path fill="currentColor" d="M15 20H5V7c0-.55-.45-1-1-1s-1 .45-1 1v13c0 1.1.9 2 2 2h10c.55 0 1-.45 1-1s-.45-1-1-1m5-4V4c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h9c1.1 0 2-.9 2-2m-2 0H9V4h9z" />
            </svg>
          </button>
        </div>
        <pre class="language-${language} !mt-0.5 rounded-b-xl"><code class="language-${language} !font-mono !text-sm">${highlighted}</code></pre>
      </div>`;
  },
});

export default md;
