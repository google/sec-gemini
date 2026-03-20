<script lang="ts">
  import { onMount } from "svelte";

  let { children } = $props();
  let container: HTMLDivElement;

  onMount(() => {
    if (!container) return;

    const textNodes: any[] = [];

    function findTextNodes(element: any) {
      if (element.nodeType === 3 && element.textContent.trim() !== "") {
        textNodes.push(element);
      } else if (element.nodeType === 1) {
        Array.from(element.childNodes).forEach((child) => findTextNodes(child));
      }
    }

    findTextNodes(container);

    let totalWordCount = 0;
    let animatedWordCount = 0;

    textNodes.forEach((textNode) => {
      const text = textNode.textContent;
      const parent = textNode.parentNode;
      const words = text.split(/(\s+)/);

      const fragment = document.createDocumentFragment();

      words.forEach((word: string, index: number) => {
        if (word.trim() === "") {
          fragment.appendChild(document.createTextNode(word));
        } else {
          const span = document.createElement("span");
          span.textContent = word;
          span.className = "word";
          span.style.animationDelay = `${totalWordCount * 0.03}s`;
          span.addEventListener("animationend", () => {
            span.classList.add("animated-finished");
            span.style.animationDelay = ``;
            animatedWordCount++;

            if (animatedWordCount === totalWordCount) {
              allWordsAnimated();
            }
          });
          fragment.appendChild(span);
          totalWordCount++;
        }
      });

      parent.replaceChild(fragment, textNode);
    });

    container.style.height = `${2.8}rem`;

    const observer = new MutationObserver(() => {
      const visibleWords = container.querySelectorAll(".animated-finished");
      if (visibleWords.length > 4) {
        const lastWord = visibleWords[visibleWords.length - 1];
        const rect = lastWord.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        const bottomPosition = rect.bottom - containerRect.top;
        container.style.height = `${bottomPosition + 8}px`;
      }
    });

    observer.observe(container, {
      subtree: true,
      attributes: true,
      attributeFilter: ["class"],
    });

    function allWordsAnimated() {
      container.classList.add("animation-completed");
      revealFeedbackElements();
    }

    function revealFeedbackElements() {
      const feedbackElement = container.nextElementSibling;
      if (feedbackElement && feedbackElement.classList.contains("feedback")) {
        feedbackElement.classList.remove("hidden");
        if (!feedbackElement.classList.contains("flex")) {
          feedbackElement.classList.add("flex");
        }
      } else {
        console.log(
          "The next sibling element is not the expected .feedback div, or it doesn't exist."
        );
      }
    }
  });
</script>

<div
  class="content-container overflow-hidden transition-[height] ease-out duration-200 prose-li:marker:text-base prose-li:has-[span.animated-finished]:marker:text-text-muted prose-li:has-[>a>span.animated-finished]:marker:text-text-muted text-text"
  bind:this={container}
>
  {@render children()}
</div>
<style>
  :global(.word) {
    display: inline-block;
    visibility: hidden;
    animation: wordAppear 0.1s ease-out forwards;
  }
  @keyframes wordAppear {
    100% {
      visibility: visible;
    }
  }
</style>
