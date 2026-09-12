// PropertyStack chat panel -- right-side slide-out shell around the chat app
// (Open WebUI in production, the stand-in page in tests). Loaded on all 5
// pages via app.js's renderShell(). See PLAN-v6.md Part W.
(function () {
  const STORAGE_OPEN = "propertystack.chatPanelOpen";

  function isOpen() {
    return sessionStorage.getItem(STORAGE_OPEN) === "1";
  }

  function setOpen(v) {
    sessionStorage.setItem(STORAGE_OPEN, v ? "1" : "0");
  }

  function markChatTabActive(active) {
    const navChat = document.querySelector(".sidebar nav a.nav-chat");
    if (navChat) navChat.classList.toggle("active", active);
  }

  function buildPanel() {
    const existing = document.getElementById("chat-panel");
    if (existing) return existing;

    const panel = document.createElement("div");
    panel.id = "chat-panel";
    panel.className = "chat-panel";
    panel.innerHTML = `
      <div class="chat-panel-header">
        <span class="chat-panel-title">✦ Ask PropertyStack</span>
        <a class="chat-panel-fullpage" href="${CHAT_APP_URL}" target="_blank" rel="noopener">Open in full page</a>
        <button class="chat-panel-close" id="chat-panel-close" aria-label="Close chat panel">&times;</button>
      </div>
      <div class="chat-panel-body">
        <div class="chat-panel-loading" id="chat-panel-loading">Loading chat…</div>
        <iframe id="chat-panel-frame" class="chat-panel-frame" title="Ask PropertyStack chat"></iframe>
        <div class="chat-panel-error" id="chat-panel-error" style="display:none;">
          Couldn't load the chat. <a href="${CHAT_APP_URL}" target="_blank" rel="noopener">Open it in a new tab</a> instead.
        </div>
      </div>
    `;
    document.body.appendChild(panel);

    const frame = panel.querySelector("#chat-panel-frame");
    const loading = panel.querySelector("#chat-panel-loading");
    const errorEl = panel.querySelector("#chat-panel-error");
    let loaded = false;

    frame.addEventListener("load", () => {
      loaded = true;
      loading.style.display = "none";
      errorEl.style.display = "none";
      frame.style.display = "block";
    });

    setTimeout(() => {
      if (!loaded) {
        loading.style.display = "none";
        errorEl.style.display = "flex";
      }
    }, 8000);

    panel.querySelector("#chat-panel-close").addEventListener("click", closePanel);

    return panel;
  }

  function ensureFrameLoaded(panel) {
    const frame = panel.querySelector("#chat-panel-frame");
    if (!frame.getAttribute("src")) frame.setAttribute("src", CHAT_APP_URL);
  }

  function openPanel() {
    const panel = buildPanel();
    ensureFrameLoaded(panel);
    panel.classList.add("open");
    document.body.classList.add("chat-panel-open");
    setOpen(true);
    markChatTabActive(true);
  }

  function closePanel() {
    const panel = document.getElementById("chat-panel");
    if (panel) panel.classList.remove("open");
    document.body.classList.remove("chat-panel-open");
    setOpen(false);
    markChatTabActive(false);
  }

  function togglePanel() {
    if (isOpen()) closePanel();
    else openPanel();
  }

  function wireTriggers() {
    document.querySelectorAll("[data-chat-toggle]").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        togglePanel();
      });
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isOpen()) closePanel();
  });

  function initChatPanel() {
    wireTriggers();
    if (isOpen()) openPanel();
  }

  window.PSChatPanel = { open: openPanel, close: closePanel, toggle: togglePanel, isOpen };
  window.initChatPanel = initChatPanel;
})();
