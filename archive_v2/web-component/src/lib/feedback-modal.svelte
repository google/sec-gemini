<script lang="ts">
    import MaterialSymbolsClose from "../icons/MaterialSymbolsClose.svelte";
  
    // Props
    let {
      id,
      groupId,
      feedbackType = "dislike",
      content,
      setFeedbackHistory,
      feedbackHistory,
      session
    } = $props();
  
    // State variables
    let feedbackDialog: HTMLDialogElement;
    let feedbackText = $state("");
    let selectedCategory = $state("");
    let isLoading = $state(false);
  
    // Categories based on feedback type
    const categories = $derived(
      feedbackType === "like"
        ? ["Helpful", "Accurate", "Clear", "Thoughtful", "Other"]
        : [
            "Problem with the app",
            "Inaccurate retrieval of items",
            "Not factually true",
            "Didn't follow instructions",
            "Other",
          ]
    );
  
    function saveFeedbackToStorage(feedbackData: { messageId: string; type: string; }) {
      setFeedbackHistory([...feedbackHistory, feedbackData]);
      try {
        if (typeof localStorage === "undefined") {
          console.error("Local storage is not available.");
        //   toast.push("Please enable local storage to allow feedback history");
        } else {
          localStorage.setItem(
            "feedbackHistory",
            JSON.stringify(feedbackHistory)
          );
        }
      } catch (error) {
        console.error("Error saving feedback to localStorage:", error);
      }
    }
  
    function closeModal() {
      if (feedbackDialog) {
        feedbackDialog.close();
      }
    }
  
    async function handleSubmitFeedback() {
      if (!selectedCategory) {
        return;
      }
  
      try {
        isLoading = true;
  
        const feedbackData = {
          messageId: groupId,
          type: feedbackType,
        };
  
        console.log("Submitting feedback:", feedbackData);
  
        await session.sendFeedback(
          feedbackType === "dislike" ? 0 : 1,
          `<feedback><score>${feedbackType === "dislike" ? 0 : 1}</score>
             <reason>${selectedCategory + " " + feedbackText}</reason>
             <message>${content}</message>
             </feedback>`,
          groupId
        );
  
        saveFeedbackToStorage(feedbackData);
  
        // toast.push(`Feedback submitted. Thank you!`);
        closeModal();
        feedbackText = "";
        selectedCategory = "";
      } catch (error) {
        console.error("Error submitting feedback:", error);
        // toast.push("Failed to submit feedback. Please try again.");
      } finally {
        isLoading = false;
      }
    }
  
    function handleClickOutside(event: Event) {
      if (feedbackDialog && event.target === feedbackDialog) {
        closeModal();
      }
    }
  </script>
  
  <dialog
    onclick={handleClickOutside}
    bind:this={feedbackDialog}
    {id}
    class="not-prose fixed inset-0 left-1/2 top-1/4 z-50 w-screen max-w-lg -translate-x-1/2 translate-y-0 opacity-0 transform bg-accent rounded-3xl text-text backdrop:backdrop-blur-xs backdrop:bg-base/50 backdrop-blur-lg transition-[overlay,display,opacity] duration-300 transition-discrete backdrop:transition-[overlay,display,opacity] backdrop:duration-300 backdrop:transition-discrete open:block open:opacity-100 open:starting:opacity-0"
  >
    <form method="dialog" class="space-y-4 not-prose p-6">
      <div class="flex justify-between items-start">
        <h2 class="text-xl font-semibold">
          {feedbackType === "like" ? "What did you like?" : "What was wrong?"}
        </h2>
        <button
          type="button"
          class="hover:opacity-90 hover:cursor-pointer hover:bg-accent rounded-full p-2 focus:outline-none -translate-y-2"
          onclick={closeModal}
          aria-label="close"
        >
          <MaterialSymbolsClose size={1.2} class="text-text" />
        </button>
      </div>
  
      <div class="mb-4">
        <p class="block text-sm font-medium mb-2">Category (required):</p>
        <div class="flex flex-wrap gap-2">
          {#each categories as category}
            <button
              type="button"
              class="px-3 py-1.5 rounded-full hover:cursor-pointer text-sm border border-accent-light hover:bg-base transition-colors {selectedCategory ===
              category
                ? 'bg-base text-text-blue'
                : ''}"
              onclick={() => (selectedCategory = category)}
            >
              {category}
            </button>
          {/each}
        </div>
      </div>
  
      <div>
        <label for="feedback-text-{id}" class="block text-sm font-medium mb-2">
          Additional details (optional):
        </label>
        <textarea
          id="feedback-text-{id}"
          class="mt-1 block w-full bg-accent-light px-3 py-2 rounded-xl"
          bind:value={feedbackText}
          placeholder="Tell us more about your feedback..."
          rows="4"
        ></textarea>
      </div>
  
      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="hover:cursor-pointer rounded-full text-text-muted py-2 px-4 text-sm font-medium hover:bg-accent-light focus:outline-none focus:ring-2 focus:ring-text focus:ring-offset-2"
          onclick={closeModal}
        >
          Cancel
        </button>
        <button
          type="button"
          class="hover:cursor-pointer min-w-44 flex gap-2 text-text-blue justify-center rounded-full hover:bg-accent-light bg-base disabled:text-text py-2 px-4 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-primary focus:ring-offset-1 disabled:opacity-50 disabled:hover:bg-base disabled:cursor-not-allowed"
          onclick={handleSubmitFeedback}
          disabled={isLoading || !selectedCategory}
        >
          {#if isLoading}
            <span class="gradient">Submitting...</span>
          {:else}
            <span>Submit Feedback</span>
          {/if}
        </button>
      </div>
    </form>
  </dialog>