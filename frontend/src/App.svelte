<script>
  import MqttLogger from "./lib/MqttLogger.svelte";
  import S3Browser from "./lib/S3Browser.svelte";
  import ToolsManager from "./lib/ToolsManager.svelte";
  import Dashboard from "./lib/Dashboard.svelte";
  import SpeakerEnroll from "./lib/SpeakerEnroll.svelte";

  let currentPage = "dashboard";
  let isMenuOpen = false; // Toggle for mobile drawer

  const navItems = [
    { id: "dashboard", name: "Dashboard", icon: "📊" },
    { id: "logs", name: "Live Logs", icon: "📡" },
    { id: "storage", name: "S3 Storage", icon: "🗄️" },
    { id: "tools", name: "Tools & Cache", icon: "⚙️" },
    { id: "enroll", name: "Enrollment", icon: "👤" },
  ];

  function navigate(id) {
    currentPage = id;
    isMenuOpen = false; // Auto-close menu on mobile after clicking
  }
</script>

<div class="app-layout">
  <header class="mobile-header">
    <button class="menu-toggle" on:click={() => (isMenuOpen = !isMenuOpen)}>
      {isMenuOpen ? "✕" : "☰"}
    </button>
    <span class="mobile-title">Voice Assistant</span>
  </header>

  <aside class="sidebar" class:open={isMenuOpen}>
    <div class="logo">
      <span class="icon">🎙️</span>
      <h1>Voice Assistant</h1>
    </div>

    <nav>
      {#each navItems as item}
        <button
          class="nav-btn"
          class:active={currentPage === item.id}
          on:click={() => navigate(item.id)}
        >
          <span class="nav-icon">{item.icon}</span>
          {item.name}
        </button>
      {/each}
    </nav>
  </aside>

  {#if isMenuOpen}
    <div class="sidebar-overlay" on:click={() => (isMenuOpen = false)}></div>
  {/if}

  <main class="content">
    <div class="page-fade-in">
      {#if currentPage === "dashboard"}
        <Dashboard />
      {:else if currentPage === "logs"}
        <MqttLogger />
      {:else if currentPage === "storage"}
        <S3Browser />
      {:else if currentPage === "tools"}
        <ToolsManager />
      {:else if currentPage === "enroll"}
        <SpeakerEnroll />
      {/if}
    </div>
  </main>
</div>

<style>
  /* --- RESPONSIVE LAYOUT --- */
  .app-layout {
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }

  .mobile-header {
    display: none; /* Hidden on desktop */
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: #111827;
    color: white;
    align-items: center;
    padding: 0 1rem;
    z-index: 40;
  }

  /* --- SIDEBAR LOGIC --- */
  .sidebar {
    width: 260px;
    background-color: #111827;
    color: white;
    display: flex;
    flex-direction: column;
    z-index: 50;
    transition: transform 0.3s ease-in-out;
  }

  .content {
    flex-grow: 1;
    background-color: #ffffff;
    padding: 2rem;
    overflow-y: auto;
    width: 100%;
  }

  /* --- MOBILE MEDIA QUERY --- */
  @media (max-width: 768px) {
    .mobile-header {
      display: flex;
    }

    .sidebar {
      position: fixed;
      left: 0;
      top: 0;
      bottom: 0;
      transform: translateX(-100%); /* Hide off-screen */
    }

    .sidebar.open {
      transform: translateX(0); /* Slide in */
    }

    .sidebar-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      z-index: 45;
    }

    .content {
      padding: 1rem;
      padding-top: 80px; /* Space for mobile header */
    }

    .menu-toggle {
      background: none;
      border: none;
      color: white;
      font-size: 1.5rem;
      cursor: pointer;
      margin-right: 1rem;
    }
    nav {
      display: flex;
      flex-direction: column;
    }
  }

  /* Keep existing .nav-btn and .logo styles from previous App.svelte... */
</style>
