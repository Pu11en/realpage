// PropertyStack chat panel -- right-side slide-out shell around the chat app
// (Open WebUI in production, the stand-in page in tests). Loaded on all 5
// pages via app.js's renderShell(). See PLAN-v6.md Part W.
(function () {
  // Guard against the script itself running twice on one page (a stray
  // duplicate <script src="js/chat-panel.js"> tag, or a caching glitch that
  // re-injects it): a second execution would attach a second set of click
  // listeners to the same Ask/Chat buttons and build a second header bar the
  // instant the first one is removed and re-added, which showed up live as
  // two "Ask CraneSignal" bars stacked for a frame. Only the first execution
  // does anything; window.initChatPanel/PSChatPanel keep pointing at it.
  if (window.__chatPanelLoaded) return;
  window.__chatPanelLoaded = true;

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
    // Belt-and-suspenders: if more than one #chat-panel ever ends up in the
    // DOM (shouldn't happen given the guards above, but this is exactly the
    // symptom -- two stacked header bars), keep only the first and drop the
    // rest instead of building yet another one.
    const stray = document.querySelectorAll("#chat-panel");
    if (stray.length > 1) stray.forEach((el, i) => i > 0 && el.remove());
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
        <div class="chat-panel-loading" id="chat-panel-loading">Waking up the chat…</div>
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
        <div class="chat-panel-deepdive-notice" id="chat-panel-deepdive-notice" style="display:none;">
          <p id="chat-panel-deepdive-text"></p>
          <button class="chat-panel-deepdive-redo" id="chat-panel-deepdive-redo" aria-label="Redo this deep dive">&#8635; Redo it</button>
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
    // The chat app is often asleep (Railway free tier) and can take well
    // over 8s to wake, so wait longer and retry once automatically before
    // giving up and showing the manual "Try again" button.
    const loadTimeoutMs = window.PS_CHAT_LOAD_TIMEOUT_MS || 30000;
    let loadTimer = null;
    let autoRetried = false;
    const startLoadTimer = () => {
      clearTimeout(loadTimer);
      loadTimer = setTimeout(() => {
        if (loaded) return;
        if (!autoRetried) {
          autoRetried = true;
          frame.setAttribute("src", CHAT_APP_URL);
          startLoadTimer();
          return;
        }
        loading.style.display = "none";
        errorEl.style.display = "flex";
      }, loadTimeoutMs);
    };
    startLoadTimer();

    panel.querySelector("#chat-panel-retry").addEventListener("click", () => {
      loaded = false;
      autoRetried = false;
      errorEl.style.display = "none";
      frame.style.display = "none";
      loading.style.display = "flex";
      frame.setAttribute("src", CHAT_APP_URL);
      startLoadTimer();
    });

    panel.querySelector("#chat-panel-close").addEventListener("click", closePanel);

    panel.querySelector("#chat-panel-deepdive-redo").addEventListener("click", () => {
      const id = panel.dataset.deepDiveId;
      const text = panel.dataset.deepDiveText;
      if (!id || !text) return;
      hideDeepDiveNotice(panel);
      frame.style.display = "block";
      sendDeepDive(panel, text);
      rememberDeepDive(id, text);
    });

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
          setSignOutVisible(false);
          return;
        }
        return fetch(`${base}/api/v1/auths/`, { credentials: "include" })
          .then((res) => {
            card.style.display = res.ok ? "none" : "flex";
            setSignOutVisible(res.ok);
          })
          .catch(() => {
            card.style.display = "flex";
            setSignOutVisible(false);
          });
      });
  }

  // T3: the sign-out link in the site header only makes sense once someone
  // could actually be signed in (live, with auth on, and currently signed
  // in). Local dev runs the chat app with auth off, so it stays hidden there.
  function setSignOutVisible(visible) {
    const link = document.getElementById("sign-out-link");
    if (link) link.style.display = visible ? "" : "none";
  }

  function signOut() {
    const base = CHAT_APP_URL.replace(/\/$/, "");
    fetch(`${base}/api/v1/auths/signout`, { method: "POST", credentials: "include" })
      .catch(() => {})
      .then(() => {
        sessionStorage.removeItem(STORAGE_OPEN);
        setSignOutVisible(false);
        location.href = `${base}/auth`;
      });
  }

  function wireSignOut() {
    const link = document.getElementById("sign-out-link");
    if (!link || link.dataset.signOutWired) return;
    link.dataset.signOutWired = "1";
    link.addEventListener("click", (e) => {
      e.preventDefault();
      signOut();
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
    hideDeepDiveNotice(panel);
    panel.querySelector("#chat-panel-frame").style.display = alreadyLoaded ? "block" : "";
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
      // renderShell() calls initChatPanel() again on view-as changes and the
      // like; without this flag a repeat call would add a second click
      // listener to the same Ask/Chat button, so one click opened then
      // immediately closed the panel (and briefly rendered a second header
      // while the first was being torn down).
      if (el.dataset.chatWired) return;
      el.dataset.chatWired = "1";
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

  const DEEPDIVE_PREFIX = "propertystack.deepDive.";

  function deepDiveKey(id) {
    return DEEPDIVE_PREFIX + id;
  }

  // T6: a repeat "Deep dive in chat" click on the same building used to just
  // reopen the same unsent question, discarding the fact it had already been
  // asked and answered. Remember the last deep dive sent per building (id,
  // prompt text and when) so a second click on the same building with the
  // same prompt shows an instant "Saved deep dive from <date>" notice with a
  // redo button, instead of silently re-typing the question.
  function savedDeepDive(id) {
    try {
      const raw = localStorage.getItem(deepDiveKey(id));
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function rememberDeepDive(id, text) {
    try {
      localStorage.setItem(deepDiveKey(id), JSON.stringify({ text, ts: Date.now() }));
    } catch (e) {
      // storage unavailable (private mode, quota) -- just skip remembering.
    }
  }

  function fmtSavedDate(ts) {
    return new Date(ts).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  }

  function hideDeepDiveNotice(panel) {
    const notice = panel.querySelector("#chat-panel-deepdive-notice");
    if (notice) notice.style.display = "none";
  }

  // Open WebUI 0.11 takes postMessage {type:"input:prompt"} only from its own
  // origin (true live, where site and chat share an address), so use that
  // when possible; otherwise (local :8765 -> :3000) load /?q=...&submit=false,
  // which fills the input without sending. See chatbot/README.md.
  function sendDeepDive(panel, text) {
    const frame = panel.querySelector("#chat-panel-frame");
    const base = CHAT_APP_URL.replace(/\/$/, "");
    const sameOrigin = new URL(base, location.href).origin === location.origin;
    const loaded = !!frame.getAttribute("src");
    if (sameOrigin && loaded && frame.contentWindow) {
      frame.contentWindow.postMessage({ type: "input:prompt", text }, location.origin);
    } else {
      frame.setAttribute("src", `${base}/?q=${encodeURIComponent(text)}&submit=false`);
    }
  }

  // "Deep dive in chat": open the panel with a prompt typed in, not sent --
  // unless this exact building/question was already deep-dived, in which
  // case show the saved-copy notice instead of retyping the question.
  function deepDive(id, text) {
    const panel = buildPanel();
    openPanel();
    const saved = savedDeepDive(id);
    panel.dataset.deepDiveId = id;
    panel.dataset.deepDiveText = text;
    if (saved && saved.text === text) {
      panel.querySelector("#chat-panel-frame").style.display = "none";
      panel.querySelector("#chat-panel-deepdive-text").textContent =
        `Saved deep dive from ${fmtSavedDate(saved.ts)}. Press ↻ to redo it.`;
      panel.querySelector("#chat-panel-deepdive-notice").style.display = "flex";
      return;
    }
    hideDeepDiveNotice(panel);
    panel.querySelector("#chat-panel-frame").style.display = "block";
    sendDeepDive(panel, text);
    rememberDeepDive(id, text);
  }

  // Plain words for a lead's stage. Covers the state files (permitted, planned,
  // under construction, leasing, sold) and the Plano property stages (zoning-filed, ...).
  const STAGE_WORDS = {
    planned: "planned", "zoning-filed": "planned", "zoning-approved": "planned",
    "site-plan-approved": "planned", permitted: "permit filed", permit: "permit filed",
    "under construction": "under construction", "under-construction": "under construction",
    leasing: "leasing now", sold: "recently sold",
  };

  function stageWords(p) {
    if (p.signalType === "Leasing" || p.stage === "leasing") return "leasing now";
    return STAGE_WORDS[p.stage] || (p.signalType === "Planned" ? "planned" : "");
  }

  function deepDivePrompt(p) {
    const units = p.units != null ? `${p.units} units` : "units not stated";
    const stage = stageWords(p);
    const upcoming = p.upcoming != null ? p.upcoming
      : (p.stage ? p.stage !== "sold" : ["Upcoming", "Planned", "Leasing"].includes(p.signalType));
    if (upcoming) {
      const bits = [units, stage || "not open yet", "software not chosen yet"].join(", ");
      const ask = stage === "leasing now" ? "who is leasing it, how full is it" : "who is developing it, when does it open";
      return `Deep dive on ${p.name}, ${p.city} (${bits}): ${ask}, and why call now?`;
    }
    const sw = p.software && p.software !== "unknown" ? p.software : "software unknown";
    const sold = stage === "recently sold" ? ", recently sold" : "";
    return `Deep dive on ${p.name}, ${p.city} (${units}, ${sw}${sold}): who runs it, and why would they switch now?`;
  }

  window.PSChatPanel = { open: openPanel, close: closePanel, toggle: togglePanel, isOpen, deepDive, deepDivePrompt };
  window.initChatPanel = initChatPanel;
  window.wireSignOut = wireSignOut;
})();
