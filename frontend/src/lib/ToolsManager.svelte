<script>
  import ToolDefinitions from "./ToolDefinitions.svelte";
  import SemanticCache from "./SemanticCache.svelte";
  import VocabManager from "./VocabManager.svelte";

  let activeTab = "tools"; // 'tools', 'cache', 'vocab'
</script>

<div class="manager-container">
  <div class="header">
    <h2>Assistant Capabilities</h2>
    <p>Manage the brains and routing of your voice assistant.</p>

    <div class="tab-menu">
      <button
        class:active={activeTab === "tools"}
        on:click={() => (activeTab = "tools")}
      >
        🛠️ Tool Definitions
      </button>
      <button
        class:active={activeTab === "cache"}
        on:click={() => (activeTab = "cache")}
      >
        🧠 Semantic Cache
      </button>
      <button
        class:active={activeTab === "vocab"}
        on:click={() => (activeTab = "vocab")}
      >
        📝 STT Vocabulary
      </button>
    </div>
  </div>

  <div class="tab-content">
    {#if activeTab === "tools"}
      <ToolDefinitions />
    {:else if activeTab === "cache"}
      <SemanticCache />
    {:else if activeTab === "vocab"}
      <VocabManager />
    {/if}
  </div>
</div>

<style>
  .manager-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  .header h2 {
    margin: 0 0 0.25rem 0;
  }
  .header p {
    margin: 0;
    color: #6b7280;
    font-size: 0.95rem;
  }

  .tab-menu {
    display: flex;
    gap: 0.5rem;
    margin-top: 1.5rem;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.5rem;
  }

  .tab-menu button {
    background: transparent;
    border: none;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    color: #6b7280;
    cursor: pointer;
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s;
  }

  .tab-menu button:hover {
    background: #f3f4f6;
    color: #111827;
  }
  .tab-menu button.active {
    background: #e0e7ff;
    color: #4f46e5;
  }
  .tab-content {
    margin-top: 1rem;
  }
</style>
