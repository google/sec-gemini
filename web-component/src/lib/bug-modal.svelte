<script>
    import MaterialSymbolsClose from "../icons/MaterialSymbolsClose.svelte";
  
    // Props
    let { id, groupId, session } = $props();
  
    // State variables
    let reportBugDialog;
    let bugDescription = $state("");
    let selectedCategory = $state("");
    let isLoading = $state(false);
  
    // Bug categories
    const categories = [
      "Incorrect Information",
      "Missing Information",
      "Poor Formatting",
      "Performance Issues",
      "Other",
    ];
  
    function closeModal() {
      if (reportBugDialog) {
        reportBugDialog.close();
      }
    }
  
    async function handleSubmitReport() {
      if (!selectedCategory) {
        // toast.push("Please select a category");
        return;
      }
  
      if (!bugDescription.trim()) {
        // toast.push("Please provide a description of the bug");
        return;
      }
  
      try {
        isLoading = true;
        console.log("Submitting bug report:", {
          messageId: groupId,
          category: selectedCategory,
          description: bugDescription,
        });
  
        await session
          .get()
          .sendBugReport(
            `Bug Report - Category: ${selectedCategory}, Description: ${bugDescription}`,
            groupId
          );
        toast.push(`Bug reported. Thank you!`);
        closeModal();
        bugDescription = "";
        selectedCategory = "";
      } catch (error) {
        console.error("Error submitting bug report:", error);
        toast.push("Failed to submit bug report. Please try again.");
      } finally {
        isLoading = false;
      }
    }
  
    function handleClickOutside(event) {
      if (reportBugDialog && event.target === reportBugDialog) {
        closeModal();
      }
    }
  </script>
  
  <dialog
    onclick={handleClickOutside}
    bind:this={reportBugDialog}
    {id}
    class="not-prose fixed inset-0 left-1/2 top-1/4 z-50 w-screen max-w-lg -translate-x-1/2 translate-y-0 opacity-0 transform bg-accent p-6 rounded-3xl text-text backdrop:backdrop-blur-xs backdrop:bg-base/50 backdrop-blur-lg transition-[overlay,display,opacity] duration-300 transition-discrete backdrop:transition-[overlay,display,opacity] backdrop:duration-300 backdrop:transition-discrete open:block open:opacity-100 open:starting:opacity-0"
  >
    <form method="dialog" class="space-y-4 not-prose">
      <div class="flex justify-between items-start">
        <h2 class="text-xl font-semibold">Report a Bug</h2>
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
        <p class="block text-sm font-medium mb-2">Category:</p>
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
        <label for="bug-description-{id}" class="block text-sm font-medium mb-2">
          Describe the bug:
        </label>
        <textarea
          id="bug-description-{id}"
          class="mt-1 block w-full bg-accent-light px-3 py-2 rounded-xl"
          bind:value={bugDescription}
          placeholder="Please describe the bug in detail..."
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
          onclick={handleSubmitReport}
          disabled={isLoading || !selectedCategory || !bugDescription.trim()}
        >
          {#if isLoading}
            <span class="gradient">Submitting...</span>
          {:else}
            <span>Report Bug</span>
          {/if}
        </button>
      </div>
    </form>
  </dialog>