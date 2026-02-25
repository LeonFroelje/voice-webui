<script>
  import { onMount, onDestroy } from "svelte";

  let stats = {
    uptime: 0,
    cpu: 0,
    ram_usage: 0,
    ram_total: 0,
    disk_usage: 0,
    disk_free: 0,
    services: {},
  };

  let interval;

  async function fetchStats() {
    try {
      const res = await fetch("/api/system/stats");
      if (res.ok) stats = await res.json();
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  }

  function formatUptime(seconds) {
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor((seconds % (3600 * 24)) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${d}d ${h}h ${m}m`;
  }

  onMount(() => {
    fetchStats();
    interval = setInterval(fetchStats, 5000); // Update every 5 seconds
  });

  onDestroy(() => clearInterval(interval));
</script>

<div class="dashboard">
  <div class="header">
    <h2>System Health</h2>
    <span class="uptime">Uptime: {formatUptime(stats.uptime)}</span>
  </div>

  <div class="stats-grid">
    <div class="card">
      <div class="card-title">CPU Load</div>
      <div class="value">{stats.cpu}%</div>
      <div class="progress-bar">
        <div
          class="fill"
          style="width: {stats.cpu}%"
          class:warn={stats.cpu > 70}
        ></div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Memory ({stats.ram_total} GB)</div>
      <div class="value">{stats.ram_usage}%</div>
      <div class="progress-bar">
        <div
          class="fill"
          style="width: {stats.ram_usage}%"
          class:warn={stats.ram_usage > 80}
        ></div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Disk Free</div>
      <div class="value">{stats.disk_free} GB</div>
      <div class="progress-bar">
        <div class="fill" style="width: {stats.disk_usage}%"></div>
      </div>
    </div>
  </div>

  <h3>Active Satellites & Services</h3>
  <div class="services-list">
    <div class="service-row">
      <span class="status-led online"></span>
      <span class="name">Main Controller (FastAPI)</span>
      <span class="tag">Online</span>
    </div>
    <div class="service-row">
      <span class="status-led online"></span>
      <span class="name">MQTT Broker (Mosquitto)</span>
      <span class="tag">Connected</span>
    </div>
    <div class="service-row">
      <span class="status-led online"></span>
      <span class="name">Garage S3 Storage</span>
      <span class="tag">Healthy</span>
    </div>
  </div>
</div>

<style>
  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }
  .uptime {
    font-family: monospace;
    color: #6b7280;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
  }

  .card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .card-title {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 0.5rem;
    font-weight: 600;
  }
  .value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 1rem;
  }

  .progress-bar {
    height: 8px;
    background: #f3f4f6;
    border-radius: 4px;
    overflow: hidden;
  }
  .fill {
    height: 100%;
    background: #3b82f6;
    transition: width 0.5s ease;
  }
  .fill.warn {
    background: #ef4444;
  }

  .services-list {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    overflow: hidden;
  }

  .service-row {
    display: flex;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #f3f4f6;
    gap: 1rem;
  }

  .service-row:last-child {
    border-bottom: none;
  }

  .status-led {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }
  .online {
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
  }

  .name {
    flex-grow: 1;
    font-weight: 500;
  }
  .tag {
    font-size: 0.75rem;
    padding: 2px 8px;
    background: #f3f4f6;
    border-radius: 4px;
    color: #6b7280;
  }
</style>
