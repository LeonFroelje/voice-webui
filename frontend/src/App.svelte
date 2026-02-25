<script>
  import MqttLogger from "./lib/MqttLogger.svelte";
  import S3Browser from "./lib/S3Browser.svelte";
  import ToolsManager from "./lib/ToolsManager.svelte";
  import Dashboard from "./lib/Dashboard.svelte";
  import SpeakerEnroll from "./lib/SpeakerEnroll.svelte";

  // State to track which page we are on
  let currentPage = "logs";

  const navItems = [
    { id: "dashboard", name: "Dashboard", icon: "📊" },
    { id: "speaker_enroll", name: "Speaker enroll", icon: "👤" },
    { id: "logs", name: "Live Logs", icon: "📡" },
    { id: "storage", name: "S3 Storage", icon: "🗄️" },
    { id: "tools", name: "Tools & Cache", icon: "⚙️" },
  ];
</script>

<div class="app-layout">
  <aside class="sidebar">
    <div class="logo">
      <span class="icon">🎙️</span>
      <h1>Voice Assistant</h1>
    </div>

    <nav>
      {#each navItems as item}
        <button
          class="nav-btn"
          class:active={currentPage === item.id}
          on:click={() => (currentPage = item.id)}
        >
          <span class="nav-icon">{item.icon}</span>
          {item.name}
        </button>
      {/each}
    </nav>

    <div class="sidebar-footer">
      <span class="version">v1.0.0</span>
    </div>
  </aside>

  <main class="content">
    {#if currentPage === "dashboard"}
      <Dashboard />
    {:else if currentPage === "logs"}
      <div class="page-fade-in">
        <MqttLogger />
      </div>
    {:else if currentPage === "speaker_enroll"}
      <div class="page-fade-in">
        <SpeakerEnroll />
      </div>
    {:else if currentPage === "storage"}
      <div class="page-fade-in">
        <S3Browser />
      </div>
    {:else if currentPage === "tools"}
      <div class="page-fade-in">
        <ToolsManager />
      </div>
    {/if}
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family:
      "Inter",
      system-ui,
      -apple-system,
      sans-serif;
    background-color: #f3f4f6; /* Light gray background behind the layout */
  }

  .app-layout {
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }

  /* --- SIDEBAR --- */
  .sidebar {
    width: 260px;
    background-color: #111827; /* Dark modern gray/blue */
    color: white;
    display: flex;
    flex-direction: column;
    box-shadow: 4px 0 10px rgba(0, 0, 0, 0.1);
    z-index: 10;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1.5rem;
    border-bottom: 1px solid #1f2937;
    margin-bottom: 1rem;
  }

  .logo .icon {
    font-size: 1.5rem;
  }

  .logo h1 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
    letter-spacing: 0.5px;
  }

  nav {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0 1rem;
    flex-grow: 1;
  }

  .nav-btn {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.75rem 1rem;
    background: transparent;
    border: none;
    color: #9ca3af;
    font-size: 0.95rem;
    font-weight: 500;
    text-align: left;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .nav-btn:hover {
    background: #1f2937;
    color: white;
  }

  .nav-btn.active {
    background: #3b82f6; /* Nice blue accent */
    color: white;
  }

  .sidebar-footer {
    padding: 1.5rem;
    font-size: 0.8rem;
    color: #4b5563;
    text-align: center;
  }

  /* --- CONTENT AREA --- */
  .content {
    flex-grow: 1;
    background-color: #ffffff;
    padding: 2rem;
    overflow-y: auto;
  }

  /* Simple CSS animation to make page switching feel smooth */
  .page-fade-in {
    animation: fadeIn 0.3s ease-in-out;
    height: 100%;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(5px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
