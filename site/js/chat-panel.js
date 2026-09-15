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

  // The Chat link opens and closes the panel; it is not a page, so it never
  // takes the "selected" look (only the current page's tab does). While the
  // panel is open it reads "Close chat" instead.
  function markChatTabActive(open) {
    const navChat = document.querySelector(".sidebar nav a.nav-chat");
    if (!navChat) return;
    navChat.classList.remove("active");
    navChat.setAttribute("aria-expanded", open ? "true" : "false");
    navChat.textContent = open ? "Close chat" : "Chat";
  }

  function buildPanel() {
    const existing = document.getElementById("chat-panel");
    if (existing) return existing;

    const panel = document.createElement("div");
    panel.id = "chat-panel";
    panel.className = "chat-panel";
    panel.innerHTML = `
      <div class="chat-panel-header">
        <span class="chat-panel-title">Ask CraneSignal</span>
        <button class="chat-panel-close" id="chat-panel-close" aria-label="Close chat panel">&times;</button>
      </div>
      <div class="chat-panel-body">
        <div class="chat-panel-loading" id="chat-panel-loading">Loading chat…</div>
        <iframe id="chat-panel-frame" class="chat-panel-frame" title="Ask CraneSignal chat"></iframe>
        <div class="chat-panel-error" id="chat-panel-error" style="display:none;">
          <p>Couldn't load the chat.</p>
          <button class="chat-panel-retry" id="chat-panel-retry">Try again</button>
        </div>
        <div class="chat-panel-signin-card" id="chat-panel-signin-card" style="display:none;">
          <p>Sign in free to ask a question.</p>
          <p class="chat-panel-signin-note">A small window opens. Use Google or your email. It closes by itself and the chat appears here.</p>
          <button class="chat-panel-signin" id="chat-panel-signin">Sign in free</button>
        </div>
      </div>
    `;
    document.body.appendChild(panel);

    const frame = panel.querySelector("#chat-panel-frame");
    const loading = panel.querySelector("#chat-panel-loading");
    const errorEl = panel.querySelector("#chat-panel-error");
    const signinCard = panel.querySelector("#chat-panel-signin-card");
    const signinBtn = panel.querySelector("#chat-panel-signin");
    let loaded = false;

    frame.addEventListener("load", () => {
      loaded = true;
      loading.style.display = "none";
      errorEl.style.display = "none";
      frame.style.display = "block";
      checkAuth(panel);
    });

    // The chat only ever lives in this panel: if it doesn't load, offer a
    // reload of the frame rather than sending people to a separate tab.
    const loadTimeoutMs = window.PS_CHAT_LOAD_TIMEOUT_MS || 8000;
    let loadTimer = null;
    const startLoadTimer = () => {
      clearTimeout(loadTimer);
      loadTimer = setTimeout(() => {
        if (!loaded) {
          loading.style.display = "none";
          errorEl.style.display = "flex";
        }
      }, loadTimeoutMs);
    };
    startLoadTimer();

    panel.querySelector("#chat-panel-retry").addEventListener("click", () => {
      loaded = false;
      errorEl.style.display = "none";
      frame.style.display = "none";
      loading.style.display = "flex";
      frame.setAttribute("src", CHAT_APP_URL);
      startLoadTimer();
    });

    panel.querySelector("#chat-panel-close").addEventListener("click", closePanel);

    // Google refuses to load inside a frame, so the chat app's own Google
    // button (inside the iframe) can't be used directly. Open the chat app
    // as a top-level popup instead -- Google is happy to load there -- and
    // reload the framed copy once the popup closes, so it picks up the new
    // signed-in session.
    signinBtn.addEventListener("click", () => {
      // /auth, not "/": live, "/" in a normal tab is the site home (site/Caddyfile).
      const popup = window.open(`${CHAT_APP_URL.replace(/\/$/, "")}/auth`, "ps-chat-signin", "width=480,height=700");
      if (!popup) return;
      // As soon as the sign-in counts, close the popup ourselves and show the
      // chat in the panel, so nobody is left chatting in the separate window.
      const authUrl = `${CHAT_APP_URL.replace(/\/$/, "")}/api/v1/auths/`;
      const finish = () => {
        clearInterval(timer);
        if (!popup.closed) popup.close();
        panel.querySelector("#chat-panel-signin-card").style.display = "none";
        frame.setAttribute("src", CHAT_APP_URL);
      };
      const timer = setInterval(() => {
        if (popup.closed) return finish();
        fetch(authUrl, { credentials: "include" })
          .then((res) => { if (res.ok) finish(); })
          .catch(() => {});
      }, 1000);
    });

    return panel;
  }

  // Real Open WebUI never tells the parent page its sign-in state (no
  // postMessage hook), so the panel checks for itself: a signed-in session
  // cookie lets this call succeed. If the request fails outright (network
  // error, CORS misconfigured), assume signed out and show the button
  // rather than leaving the user stuck on Google's framed (and refused)
  // login button with no way forward.
  function checkAuth(panel) {
    const card = panel.querySelector("#chat-panel-signin-card");
    const base = CHAT_APP_URL.replace(/\/$/, "");
    // Local dev runs the chat app with login turned off (tooling/dev.sh):
    // its public config says auth:false, so there's nothing to sign in to.
    fetch(`${base}/api/config`)
      .then((res) => (res.ok ? res.json() : {}))
      .catch(() => ({}))
      .then((cfg) => {
        if (cfg && cfg.features && cfg.features.auth === false) {
          card.style.display = "none";
          return;
        }
        return fetch(`${base}/api/v1/auths/`, { credentials: "include" })
          .then((res) => {
            card.style.display = res.ok ? "none" : "flex";
          })
          .catch(() => {
            card.style.display = "flex";
          });
      });
  }

  function ensureFrameLoaded(panel) {
    const frame = panel.querySelector("#chat-panel-frame");
    if (!frame.getAttribute("src")) frame.setAttribute("src", CHAT_APP_URL);
  }

  function openPanel() {
    const panel = buildPanel();
    const alreadyLoaded = !!panel.querySelector("#chat-panel-frame").getAttribute("src");
    ensureFrameLoaded(panel);
    if (alreadyLoaded) checkAuth(panel);
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

  // "Deep dive in chat": open the panel with a prompt typed in, not sent.
  // Open WebUI 0.11 takes postMessage {type:"input:prompt"} only from its own
  // origin (true live, where site and chat share an address), so use that
  // when possible; otherwise (local :8765 -> :3000) load /?q=...&submit=false,
  // which fills the input without sending. See chatbot/README.md.
  function deepDive(text) {
    const panel = buildPanel();
    const frame = panel.querySelector("#chat-panel-frame");
    const base = CHAT_APP_URL.replace(/\/$/, "");
    const sameOrigin = new URL(base, location.href).origin === location.origin;
    const loaded = !!frame.getAttribute("src");
    openPanel();
    if (sameOrigin && loaded && frame.contentWindow) {
      frame.contentWindow.postMessage({ type: "input:prompt", text }, location.origin);
    } else {
      frame.setAttribute("src", `${base}/?q=${encodeURIComponent(text)}&submit=false`);
    }
  }

  function deepDivePrompt(p) {
    const units = p.units != null ? `${p.units} units` : "units not stated";
    if (p.upcoming) {
      return `Deep dive on ${p.name}, ${p.city} (${units}, planned, software not chosen yet): who is developing it, when does it open, and why call now?`;
    }
    const sw = p.software && p.software !== "unknown" ? p.software : "software unknown";
    return `Deep dive on ${p.name}, ${p.city} (${units}, ${sw}): who runs it, and why would they switch now?`;
  }

  window.PSChatPanel = { open: openPanel, close: closePanel, toggle: togglePanel, isOpen, deepDive, deepDivePrompt };
  window.initChatPanel = initChatPanel;
})();
