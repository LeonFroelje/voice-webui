<script>
  import { onMount } from "svelte";
  let semanticCache = {};
  let isLoading = false;
  let statusMsg = "";
  let showModal = false;
  let originalKey = "";
  let form = { trigger: "", tool: "", args: "{}", exact_only: true };

  async function load() {
    isLoading = true;
    const res = await fetch("/api/config/cache");
    const json = await res.json();
    semanticCache = json.data || {};
    isLoading = false;
  }

  async function save(updated) {
    const res = await fetch("/api/config/cache", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: updated }),
    });
    if (res.ok) {
      semanticCache = updated;
      statusMsg = "Saved to S3";
      setTimeout(() => (statusMsg = ""), 3000);
    }
  }

  function openEdit(key) {
    originalKey = key;
    const entry = semanticCache[key];
    form = {
      trigger: key,
      tool: entry.tool,
      args: JSON.stringify(entry.args, null, 2),
      exact_only: entry.exact_only,
    };
    showModal = true;
  }

  function handleSave() {
    let updated = { ...semanticCache };
    if (originalKey && originalKey !== form.trigger)
      delete updated[originalKey];
    updated[form.trigger] = {
      tool: form.tool,
      args: JSON.parse(form.args),
      exact_only: form.exact_only,
    };
    save(updated);
    showModal = false;
  }

  onMount(load);
</script>

<div class="toolbar">
  <h3>Transcript Mapping ({Object.keys(semanticCache).length})</h3>
  {#if statusMsg}<span class="status">{statusMsg}</span>{/if}
</div>

<div class="cache-list">
  {#each Object.entries(semanticCache) as [trigger, data]}
    <div class="cache-row">
      <div class="info">
        <span class="trigger">"{trigger}"</span>
        <span class="tool">▶ Name: {data.tool}</span>
        <span class="tool">▶ Args: {JSON.stringify(data.args)}</span>
      </div>
      <button class="btn-edit" on:click={() => openEdit(trigger)}>Edit</button>
    </div>
  {/each}
</div>

{#if showModal}
  <div class="modal-backdrop" on:click|self={() => (showModal = false)}>
    <div class="modal">
      <h3>Edit Cache Entry</h3>
      <input bind:value={form.trigger} placeholder="Transcript" />
      <input bind:value={form.tool} placeholder="Tool Name" />
      <textarea bind:value={form.args} rows="5"></textarea>
      <label
        ><input type="checkbox" bind:checked={form.exact_only} /> Exact Match Only</label
      >
      <div class="actions">
        <button on:click={() => (showModal = false)}>Cancel</button>
        <button class="primary" on:click={handleSave}>Save</button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Same styles we used before, scoped specifically to this file */
  .cache-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .cache-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: white;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
  }
  .info {
    display: flex;
    flex-direction: column;
  }
  .trigger {
    font-weight: 600;
    font-style: italic;
  }
  .tool {
    color: #4f46e5;
    font-size: 0.9rem;
  }
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .modal {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    width: 400px;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  input,
  textarea {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  .primary {
    background: #4f46e5;
    color: white;
    border: none;
    padding: 0.5rem;
    border-radius: 4px;
    cursor: pointer;
  }
  .status {
    font-size: 0.8rem;
    color: #059669;
    margin-left: 1rem;
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
