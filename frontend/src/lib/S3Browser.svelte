<script>
  import { onMount } from "svelte";

  let files = [];
  let loading = true;
  let error = null;

  // Audio player state
  let activeAudioUrl = null;
  let activeFilename = null;

  // Fetch the file list from FastAPI
  async function fetchFiles() {
    loading = true;
    error = null;
    try {
      // The Vite proxy handles routing /api to localhost:8000
      const res = await fetch("/api/s3/files");
      if (!res.ok) throw new Error("Failed to fetch files from Garage/S3");

      const data = await res.json();
      files = data.files;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  // Replace your existing playAudio function with this simplified version:
  function playAudio(filename) {
    // We just point the audio player directly to our proxy endpoint
    activeAudioUrl = `/api/s3/stream/${encodeURIComponent(filename)}`;
    activeFilename = filename;
  }
  // Utility to format bytes into readable sizes
  function formatSize(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  // Utility to format ISO dates
  function formatDate(isoString) {
    return new Date(isoString).toLocaleString();
  }

  // Fetch files when the component mounts
  onMount(() => {
    fetchFiles();
  });
</script>

<div class="s3-container">
  <div class="header">
    <h2>S3 Audio Storage</h2>
    <button on:click={fetchFiles} disabled={loading}>
      {loading ? "Refreshing..." : "Refresh Bucket"}
    </button>
  </div>

  {#if activeAudioUrl}
    <div class="player-card">
      <p><strong>Now Playing:</strong> {activeFilename}</p>

      {#key activeAudioUrl}
        <audio controls autoplay>
          <source src={activeAudioUrl} type="audio/wav" />
          Your browser does not support the audio element.
        </audio>
      {/key}
    </div>
  {/if}
  {#if loading && files.length === 0}
    <p>Loading files from Garage...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if files.length === 0}
    <p>No audio files found in the bucket.</p>
  {:else}
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Filename</th>
            <th>Size</th>
            <th>Date Modified</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {#each files as file}
            <tr>
              <td>{file.filename}</td>
              <td>{formatSize(file.size)}</td>
              <td>{formatDate(file.last_modified)}</td>
              <td>
                {#if file.filename.includes(".wav")}
                  <button
                    class="play-btn"
                    on:click={() => playAudio(file.filename)}
                  >
                    Play
                  </button>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .s3-container {
    font-family:
      system-ui,
      -apple-system,
      sans-serif;
    padding: 1rem;
    background: #f9fafb;
    border-radius: 8px;
    color: #1f2937;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .player-card {
    background: #e5e7eb;
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
  }

  .player-card p {
    margin-top: 0;
    margin-bottom: 0.5rem;
  }

  audio {
    width: 100%;
  }

  .table-wrapper {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  th,
  td {
    text-align: left;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #e5e7eb;
  }

  th {
    background: #f3f4f6;
    font-weight: 600;
  }

  button {
    cursor: pointer;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    border: none;
    background: #3b82f6;
    color: white;
    font-weight: bold;
  }

  button:hover:not(:disabled) {
    background: #2563eb;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .play-btn {
    background: #10b981;
  }

  .play-btn:hover {
    background: #059669;
  }

  .error {
    color: #ef4444;
    font-weight: bold;
  }
</style>
