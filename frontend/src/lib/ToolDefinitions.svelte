<script>
  import { onMount } from "svelte";

  let tools = [];
  let isLoading = false;
  let showModal = false;
  let editIndex = -1;

  // Template for a new tool following your schema
  const toolTemplate = {
    type: "function",
    exact_cache_only: true,
    function: {
      name: "",
      description: "",
      parameters: {
        type: "object",
        properties: {},
        required: [],
      },
    },
  };

  let currentTool = JSON.parse(JSON.stringify(toolTemplate));
  let paramsJson = "";

  async function load() {
    isLoading = true;
    try {
      const res = await fetch("/api/config/tools");
      const json = await res.json();
      tools = Array.isArray(json.data) ? json.data : [];
    } finally {
      isLoading = false;
    }
  }

  async function save(updatedList) {
    await fetch("/api/config/tools", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: updatedList }),
    });
    tools = updatedList;
  }

  function openEdit(index) {
    editIndex = index;
    currentTool = JSON.parse(JSON.stringify(tools[index]));
    paramsJson = JSON.stringify(currentTool.function.parameters, null, 2);
    showModal = true;
  }

  function handleSave() {
    try {
      currentTool.function.parameters = JSON.parse(paramsJson);
      let updated = [...tools];
      if (editIndex === -1) updated.push(currentTool);
      else updated[editIndex] = currentTool;
      save(updated);
      showModal = false;
    } catch (e) {
      alert("Invalid JSON in Parameters field!");
    }
  }

  function deleteTool(index) {
    if (confirm("Delete this tool definition?")) {
      save(tools.filter((_, i) => i !== index));
    }
  }

  onMount(load);
</script>

<div class="tool-list-container">
  <div class="toolbar">
    <h3>LLM Tool Definitions ({tools.length})</h3>
    <button
      class="primary-btn"
      on:click={() => {
        editIndex = -1;
        currentTool = JSON.parse(JSON.stringify(toolTemplate));
        paramsJson = JSON.stringify(currentTool.function.parameters, null, 2);
        showModal = true;
      }}>+ New Tool</button
    >
  </div>

  <div class="grid">
    {#each tools as tool, i}
      <div class="tool-card">
        <div class="card-header">
          <strong>{tool.function.name}</strong>
          <span class="pill" class:exact={tool.exact_cache_only}>
            {tool.exact_cache_only ? "Exact Cache Only" : "Dynamic LLM"}
          </span>
        </div>
        <p>{tool.function.description}</p>
        <div class="params-preview">
          <span
            >Props: {Object.keys(
              tool.function.parameters.properties || {},
            ).join(", ")}</span
          >
        </div>
        <div class="actions">
          <button on:click={() => openEdit(i)}>Edit Schema</button>
          <button class="del" on:click={() => deleteTool(i)}>Delete</button>
        </div>
      </div>
    {/each}
  </div>
</div>

{#if showModal}
  <div class="modal-overlay" on:click|self={() => (showModal = false)}>
    <div class="modal">
      <h3>{editIndex === -1 ? "Define New Tool" : "Edit Tool Schema"}</h3>

      <label>Function Name</label>
      <input
        bind:value={currentTool.function.name}
        placeholder="control_light"
      />

      <label>Description</label>
      <textarea bind:value={currentTool.function.description} rows="2"
      ></textarea>

      <div class="row">
        <label>
          <input type="checkbox" bind:checked={currentTool.exact_cache_only} />
          Exact Cache Only
        </label>
      </div>

      <label>Parameters (JSON Schema)</label>
      <textarea class="code" bind:value={paramsJson} rows="12"></textarea>

      <div class="modal-btns">
        <button on:click={() => (showModal = false)}>Cancel</button>
        <button class="primary-btn" on:click={handleSave}
          >Save Definition</button
        >
      </div>
    </div>
  </div>
{/if}

<style>
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1rem;
  }
  .tool-card {
    background: #fff;
    padding: 1.25rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .pill {
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    background: #edf2f7;
    color: #4a5568;
  }
  .pill.exact {
    background: #fed7d7;
    color: #822727;
  }
  p {
    font-size: 0.85rem;
    color: #4a5568;
    margin: 0;
  }
  .params-preview {
    font-size: 0.75rem;
    font-family: monospace;
    color: #718096;
    background: #f7fafc;
    padding: 4px;
    border-radius: 4px;
  }

  .actions {
    display: flex;
    gap: 0.5rem;
    margin-top: auto;
    padding-top: 1rem;
  }
  .actions button {
    flex: 1;
    font-size: 0.8rem;
    padding: 6px;
    cursor: pointer;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    background: #fff;
  }
  .actions .del {
    color: #e53e3e;
    border-color: #feb2b2;
  }

  .primary-btn {
    background: #3182ce;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
  }

  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }
  .modal {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    width: 600px;
    max-width: 95vw;
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    max-height: 90vh;
    overflow-y: auto;
  }
  label {
    font-size: 0.8rem;
    font-weight: bold;
    color: #2d3748;
  }
  input,
  textarea {
    padding: 8px;
    border: 1px solid #cbd5e0;
    border-radius: 4px;
    font-family: inherit;
  }
  .code {
    font-family: "Fira Code", monospace;
    font-size: 0.8rem;
    background: #2d3748;
    color: #fff;
  }
  .modal-btns {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 1rem;
  }
  /* Inside your component <style> blocks */
  @media (max-width: 600px) {
    .toolbar {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .btn-primary {
      width: 100%; /* Make buttons full-width on tiny screens */
    }

    .cache-row {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>
