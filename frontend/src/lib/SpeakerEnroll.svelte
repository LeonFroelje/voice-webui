<script>
  import { onMount } from "svelte";

  let speakerId = "";
  let s3Files = [];
  let selectedS3Files = new Set();
  let isRecording = false;
  let mediaRecorder;
  let audioChunks = [];
  let enrollmentStatus = "";

  // 1. Fetch existing S3 files to "flag" them for enrollment
  async function loadS3Files() {
    const res = await fetch("/api/s3/files");
    const data = await res.json();
    s3Files = data.files.filter((f) => f.filename.endsWith(".wav"));
  }

  // 2. Browser Recording Logic
  async function toggleRecording() {
    if (!isRecording) {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
      mediaRecorder.onstop = uploadRecording;
      mediaRecorder.start();
      isRecording = true;
    } else {
      mediaRecorder.stop();
      isRecording = false;
    }
  }

  async function uploadRecording() {
    if (!speakerId) return alert("Enter Speaker ID first");
    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    const formData = new FormData();
    formData.append("speaker_id", speakerId);
    formData.append("file", audioBlob, `rec_${Date.now()}.wav`);

    const res = await fetch("/api/speaker/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    selectedS3Files.add(data.filename);
    selectedS3Files = selectedS3Files; // trigger reactivity
  }

  // 3. Trigger Training
  async function enroll() {
    if (!speakerId || selectedS3Files.size === 0)
      return alert("Missing ID or files");

    const res = await fetch(`/api/speaker/enroll?speaker_id=${speakerId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Array.from(selectedS3Files)),
    });
    enrollmentStatus =
      'Enrollment request sent! Check logs for "voice/speaker/enrolled"';
  }

  onMount(loadS3Files);
</script>

<div class="enroll-container">
  <h2>👤 Speaker Enrollment</h2>

  <div class="input-group">
    <label>Speaker ID (Unique Name)</label>
    <input type="text" bind:value={speakerId} placeholder="e.g. user_42" />
  </div>

  <div class="split">
    <div class="card">
      <h3>Record Samples</h3>
      <button
        class="record-btn"
        class:recording={isRecording}
        on:click={toggleRecording}
      >
        {isRecording ? "⏹ Stop Recording" : "🎤 Start Recording"}
      </button>
      <p>Recorded samples will be uploaded to S3 automatically.</p>
    </div>

    <div class="card">
      <h3>Flag Existing S3 Files</h3>
      <div class="file-list">
        {#each s3Files as file}
          <label class="file-item">
            <input
              type="checkbox"
              checked={selectedS3Files.has(file.filename)}
              on:change={(e) => {
                if (e.target.checked) selectedS3Files.add(file.filename);
                else selectedS3Files.delete(file.filename);
                selectedS3Files = selectedS3Files;
              }}
            />
            {file.filename}
          </label>
        {/each}
      </div>
    </div>
  </div>

  <div class="footer">
    <div class="selection-summary">
      Selected Files: {selectedS3Files.size}
    </div>
    <button
      class="enroll-btn"
      on:click={enroll}
      disabled={!speakerId || selectedS3Files.size === 0}
    >
      🚀 Start Enrollment Training
    </button>
    {#if enrollmentStatus}<p class="status">{enrollmentStatus}</p>{/if}
  </div>
</div>

<style>
  .enroll-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  .split {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }
  .card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
  }

  .input-group input {
    padding: 0.75rem;
    width: 100%;
    max-width: 300px;
    border-radius: 6px;
    border: 1px solid #ddd;
  }

  .record-btn {
    width: 100%;
    padding: 1rem;
    border-radius: 8px;
    border: none;
    background: #3b82f6;
    color: white;
    font-weight: bold;
    cursor: pointer;
  }
  .record-btn.recording {
    background: #ef4444;
    animation: pulse 1.5s infinite;
  }

  .file-list {
    max-height: 200px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    border: 1px solid #f3f4f6;
    padding: 0.5rem;
  }
  .file-item {
    display: flex;
    gap: 0.5rem;
    font-size: 0.85rem;
    cursor: pointer;
  }

  .footer {
    border-top: 1px solid #e5e7eb;
    padding-top: 1.5rem;
    text-align: center;
  }
  .enroll-btn {
    padding: 1rem 2rem;
    background: #10b981;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
  }
  .enroll-btn:disabled {
    background: #d1d5db;
    cursor: not-allowed;
  }

  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
    100% {
      opacity: 1;
    }
  }
</style>
