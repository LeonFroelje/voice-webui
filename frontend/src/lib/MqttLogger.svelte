<script>
  import { onMount, onDestroy, tick } from "svelte";

  let logs = [];
  let filterText = "";
  let ws;
  let logContainer;
  let isConnected = false;
  const MAX_LOGS = 200; // Keep browser memory usage in check

  // Try to parse payload as JSON for pretty printing
  function formatPayload(rawPayload) {
    try {
      const parsed = JSON.parse(rawPayload);
      return JSON.stringify(parsed, null, 2);
    } catch (e) {
      return rawPayload;
    }
  }

  async function fetchHistory() {
    try {
      const res = await fetch("/api/logs/history");
      if (res.ok) {
        const data = await res.json();
        // Process each historical log
        logs = data.logs.map((log) => ({
          ...log,
          payload: formatPayload(log.payload),
        }));

        // Scroll to bottom
        await tick();
        if (logContainer) logContainer.scrollTop = logContainer.scrollHeight;
      }
    } catch (err) {
      console.error("Failed to fetch log history:", err);
    }
  }

  function connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      isConnected = true;
      // Fixed system log format to match what addLog expects
      addLog({
        id: Date.now(),
        time: "SYS",
        topic: "SYSTEM",
        payload: "Connected to MQTT WebSocket bridge.",
      });
    };

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        addLog(data);
      } catch (err) {
        console.error("Failed to parse WebSocket message", err);
      }
    };

    ws.onclose = () => {
      isConnected = false;
      // Fixed system log format
      addLog({
        id: Date.now(),
        time: "SYS",
        topic: "SYSTEM",
        payload: "Disconnected. Reconnecting in 3s...",
      });
      setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      ws.close();
    };
  }

  async function addLog(logData) {
    const newLog = {
      ...logData,
      payload: formatPayload(logData.payload),
    };

    logs = [...logs, newLog].slice(-MAX_LOGS);

    await tick();
    if (logContainer) {
      logContainer.scrollTop = logContainer.scrollHeight;
    }
  }

  function clearLogs() {
    logs = [];
  }

  // Only one onMount block!
  onMount(async () => {
    await fetchHistory();
    connect();
  });

  onDestroy(() => {
    if (ws) ws.close();
  });

  // Added safety check (log.topic || "") just in case a malformed log slips through
  $: filteredLogs = logs.filter(
    (log) =>
      (log.topic || "").toLowerCase().includes(filterText.toLowerCase()) ||
      filterText === "",
  );
</script>

<div class="logger-container">
  <div class="header">
    <div class="title-area">
      <h2>Live MQTT Traffic</h2>
      <span class="status {isConnected ? 'connected' : 'disconnected'}">
        {isConnected ? "● Live" : "○ Offline"}
      </span>
    </div>

    <div class="controls">
      <input
        type="text"
        bind:value={filterText}
        placeholder="Filter by topic (e.g., voice/asr)..."
      />
      <button class="btn-clear" on:click={clearLogs}>Clear</button>
    </div>
  </div>

  <div class="terminal" bind:this={logContainer}>
    {#if filteredLogs.length === 0}
      <div class="empty-state">Waiting for messages...</div>
    {/if}

    {#each filteredLogs as log (log.id)}
      <div class="log-entry" class:system-log={log.topic === "SYSTEM"}>
        <div class="log-meta">
          <span class="time">[{log.time}]</span>
          <span class="topic">{log.topic}</span>
        </div>
        <pre class="payload">{log.payload}</pre>
      </div>
    {/each}
  </div>
</div>

<style>
  .logger-container {
    background: #f9fafb;
    padding: 1rem;
    border-radius: 8px;
    font-family: system-ui, sans-serif;
    color: #1f2937;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .title-area {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  h2 {
    margin: 0;
  }

  .status {
    font-size: 0.875rem;
    font-weight: bold;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }
  .connected {
    background: #d1fae5;
    color: #065f46;
  }
  .disconnected {
    background: #fee2e2;
    color: #991b1b;
  }

  .controls {
    display: flex;
    gap: 0.5rem;
  }

  input {
    padding: 0.5rem;
    border-radius: 4px;
    border: 1px solid #d1d5db;
    min-width: 250px;
  }

  button {
    cursor: pointer;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    border: none;
    font-weight: bold;
    color: white;
  }
  .btn-clear {
    background: #ef4444;
  }
  .btn-clear:hover {
    background: #dc2626;
  }

  .terminal {
    flex-grow: 1;
    background: #1e1e1e; /* Dark terminal look */
    color: #d4d4d4;
    border-radius: 6px;
    padding: 1rem;
    overflow-y: auto;
    font-family: "Courier New", Courier, monospace;
    font-size: 13px;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .empty-state {
    color: #858585;
    font-style: italic;
  }

  .log-entry {
    border-bottom: 1px solid #333;
    padding-bottom: 0.5rem;
  }
  .log-entry:last-child {
    border-bottom: none;
  }

  .log-meta {
    margin-bottom: 0.25rem;
  }

  .time {
    color: #569cd6;
  }
  .topic {
    color: #ce9178;
    font-weight: bold;
    margin-left: 0.5rem;
  }

  .system-log .topic {
    color: #c586c0;
  }

  .payload {
    margin: 0;
    padding-left: 1rem;
    white-space: pre-wrap; /* Wrap long JSON strings */
    word-break: break-all;
    color: #9cdcfe;
  }
</style>
