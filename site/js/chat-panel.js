// PropertyStack chat panel -- right-side slide-out shell around the chat app
// (Open WebUI in production, the stand-in page in tests). Loaded on all 5
// pages via app.js's renderShell().
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
  const DEFAULT_SIGNIN_PURPOSE = "Make a free account to see who to call.";
  let pendingAuthAction = null;

  // Open by default on every page; only an explicit close (the X) keeps it
  // shut, and only for this visit (sessionStorage).
  // Below 900px the panel floats over the whole page instead of docking, so
  // there it only opens when asked; otherwise a phone visitor would see
  // nothing but the account prompt.
  function isOpen() {
    const v = sessionStorage.getItem(STORAGE_OPEN);
    if (v === null) return window.matchMedia("(min-width: 900px)").matches;
    return v === "1";
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
          <p id="chat-panel-signin-purpose">${DEFAULT_SIGNIN_PURPOSE}</p>
          <p class="chat-panel-signin-note">Takes about 20 seconds, with Google or your email. No card. It also unlocks the agent and your Lead Pack.</p>
          <button class="chat-panel-signin" id="chat-panel-signin">Make a free account</button>
          <a href="#" class="chat-panel-signin-link" id="chat-panel-signin-link">Already have one? Sign in</a>
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
      panel.dataset.frameReady = "1";
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
          setFrameSource(panel, CHAT_APP_URL);
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
      setFrameSource(panel, CHAT_APP_URL);
      startLoadTimer();
    });

    panel.querySelector("#chat-panel-close").addEventListener("click", closePanel);

    panel.querySelector("#chat-panel-deepdive-redo").addEventListener("click", () => {
      const id = panel.dataset.deepDiveId;
      const text = panel.dataset.deepDiveText;
      if (!id || !text) return;
      hideDeepDiveNotice(panel);
      frame.style.display = "block";
      queueQuestion(panel, text, id);
    });

    // Google refuses to load inside a frame, so the chat app's own Google
    // button (inside the iframe) can't be used directly. Open the chat app
    // as a top-level popup instead -- Google is happy to load there -- and
    // reload the framed copy once the popup closes, so it picks up the new
    // signed-in session.
    const startSignIn = (e) => {
      if (e) e.preventDefault();
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
        setFrameSource(panel, CHAT_APP_URL);
        checkAuth(panel);
      };
      const timer = setInterval(() => {
        if (popup.closed) return finish();
        fetch(authUrl, { credentials: "include" })
          .then((res) => { if (res.ok) finish(); })
          .catch(() => {});
      }, 1000);
    };
    signinBtn.addEventListener("click", startSignIn);
    panel.querySelector("#chat-panel-signin-link").addEventListener("click", startSignIn);

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
    return fetch(`${base}/api/config`)
      .then((res) => (res.ok ? res.json() : {}))
      .catch(() => ({}))
      .then((cfg) => {
        if (cfg && cfg.features && cfg.features.auth === false) {
          card.style.display = "none";
          panel.dataset.canAsk = "1";
          setSignOutVisible(false);
          sendPendingQuestion(panel);
          sendPendingAuthAction(panel);
          return true;
        }
        return fetch(`${base}/api/v1/auths/`, { credentials: "include" })
          .then((res) => {
            card.style.display = res.ok ? "none" : "flex";
            panel.dataset.canAsk = res.ok ? "1" : "0";
            setSignOutVisible(res.ok);
            if (res.ok) sendPendingQuestion(panel);
            if (res.ok) sendPendingAuthAction(panel);
            return res.ok;
          })
          .catch(() => {
            card.style.display = "flex";
            panel.dataset.canAsk = "0";
            setSignOutVisible(false);
            return false;
          });
      });
  }

  function setSignInPurpose(panel, text) {
    const purpose = panel.querySelector("#chat-panel-signin-purpose");
    if (purpose) purpose.textContent = text || DEFAULT_SIGNIN_PURPOSE;
  }

  function sendPendingAuthAction(panel) {
    if (!pendingAuthAction || panel.dataset.canAsk !== "1") return false;
    const action = pendingAuthAction;
    pendingAuthAction = null;
    setSignInPurpose(panel, DEFAULT_SIGNIN_PURPOSE);
    action();
    return true;
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
        // In the same-origin human preview Open WebUI also remembers its
        // session token in this browser.  Clearing the server session alone
        // leaves that stale token to route a person straight back into the
        // app instead of showing the account screen.
        localStorage.removeItem("token");
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

  function setFrameSource(panel, url) {
    panel.dataset.frameReady = "0";
    panel.querySelector("#chat-panel-frame").setAttribute("src", url);
  }

  function ensureFrameLoaded(panel) {
    const frame = panel.querySelector("#chat-panel-frame");
    if (!frame.getAttribute("src")) setFrameSource(panel, CHAT_APP_URL);
  }

  function openPanel(signinPurpose) {
    const panel = buildPanel();
    if (signinPurpose) setSignInPurpose(panel, signinPurpose);
    else if (!pendingAuthAction) setSignInPurpose(panel, DEFAULT_SIGNIN_PURPOSE);
    const alreadyLoaded = !!panel.querySelector("#chat-panel-frame").getAttribute("src");
    ensureFrameLoaded(panel);
    // Check right away (not only after the frame loads) so a signed-out
    // visitor sees the free-account prompt without waiting for the chat app.
    checkAuth(panel);
    hideDeepDiveNotice(panel);
    panel.querySelector("#chat-panel-frame").style.display = alreadyLoaded ? "block" : "";
    panel.classList.add("open");
    document.body.classList.add("chat-panel-open");
    setOpen(true);
    markChatTabActive(true);
  }

  // Reuse the chat panel's session check for gated site actions. Signed-in
  // visitors continue immediately. Signed-out visitors see this purpose in
  // the existing account card, and the action resumes after sign-in succeeds.
  function requireAuth(purpose, onSuccess) {
    const panel = buildPanel();
    pendingAuthAction = onSuccess;
    setSignInPurpose(panel, purpose);
    return checkAuth(panel).then((signedIn) => {
      if (!signedIn) openPanel(purpose);
      return signedIn;
    });
  }

  function closePanel() {
    const panel = document.getElementById("chat-panel");
    if (panel) panel.classList.remove("open");
    document.body.classList.remove("chat-panel-open");
    setOpen(false);
    markChatTabActive(false);
  }

  function togglePanel() {
    const panel = document.getElementById("chat-panel");
    if (panel && panel.classList.contains("open")) closePanel();
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

  // T6: a repeat contact request for the same building used to just reopen
  // the same question, discarding the fact it had already been
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

  // Open WebUI 0.11 takes postMessage {type:"input:prompt:submit"} only from
  // its own origin (true live, where site and chat share an address). Locally
  // the chat is cross-origin, so use its q URL with submit=true instead.
  function sendQuestion(panel, text) {
    const frame = panel.querySelector("#chat-panel-frame");
    const base = CHAT_APP_URL.replace(/\/$/, "");
    const sameOrigin = new URL(base, location.href).origin === location.origin;
    if (sameOrigin) {
      if (panel.dataset.frameReady !== "1" || !frame.contentWindow) return false;
      frame.contentWindow.postMessage({ type: "input:prompt:submit", text }, location.origin);
    } else {
      setFrameSource(panel, `${base}/?q=${encodeURIComponent(text)}&submit=true`);
    }
    return true;
  }

  // Hold the question while a signed-out visitor creates an account. Every
  // successful auth check tries this queue, so the same waiting question is
  // sent automatically as soon as the reloaded chat is ready.
  function sendPendingQuestion(panel) {
    const text = panel.dataset.pendingQuestion;
    if (!text || panel.dataset.canAsk !== "1") return false;
    if (!sendQuestion(panel, text)) return false;
    const id = panel.dataset.pendingQuestionId;
    delete panel.dataset.pendingQuestion;
    delete panel.dataset.pendingQuestionId;
    if (id) rememberDeepDive(id, text);
    return true;
  }

  function queueQuestion(panel, text, id) {
    panel.dataset.pendingQuestion = text;
    if (id) panel.dataset.pendingQuestionId = id;
    else delete panel.dataset.pendingQuestionId;
    checkAuth(panel);
  }

  // "Get contact": open the panel and send the contact-first question. If
  // this exact building/question was already sent, show the saved-copy notice.
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
    queueQuestion(panel, text, id);
  }

  function ask(text) {
    const panel = buildPanel();
    openPanel();
    hideDeepDiveNotice(panel);
    panel.querySelector("#chat-panel-frame").style.display = "block";
    queueQuestion(panel, text);
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
    const whoToCall = "Who to call: management company, office phone, website, and the role to ask for (with a source link for each)";
    const upcoming = p.upcoming != null ? p.upcoming
      : (p.stage ? p.stage !== "sold" : ["Upcoming", "Planned", "Leasing"].includes(p.signalType));
    if (upcoming) {
      const bits = [units, stage || "not open yet", "software not chosen yet"].join(", ");
      const ask = stage === "leasing now" ? "who is leasing it, how full is it" : "who is developing it, when does it open";
      return `Deep dive on ${p.name}, ${p.city} (${bits}): ${whoToCall}. Then tell me ${ask}, and why call now.`;
    }
    const sw = p.software && p.software !== "unknown" ? p.software : "software unknown";
    const sold = stage === "recently sold" ? ", recently sold" : "";
    const newOwner = stage === "recently sold" && !p.buyer ? " Also find who bought it (new owner), with a source link." : "";
    return `Deep dive on ${p.name}, ${p.city} (${units}, ${sw}${sold}): ${whoToCall}.${newOwner} Then tell me why call now and why they might switch.`;
  }

  window.PSChatPanel = { open: openPanel, close: closePanel, toggle: togglePanel, isOpen, ask, deepDive, deepDivePrompt, requireAuth };
  window.initChatPanel = initChatPanel;
  window.wireSignOut = wireSignOut;
})();
