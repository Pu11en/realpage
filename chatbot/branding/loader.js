// CraneSignal: the chat app only lives inside the dashboard's side panel.
// Open WebUI loads /static/loader.js on every page. If one of its pages is opened
// on its own (not framed, not the sign-in popup), send the visitor to the dashboard.
// /auth stays usable on its own for signing in; once it moves on to the chat home,
// we go to the dashboard instead. /admin stays open for the owner.
// Light is the default look (same as the dashboard). Open WebUI's own head script has
// already stored "system" by now, so apply light once per browser and remember we did;
// a theme the visitor picks later in Open WebUI's settings is kept.
(function () {
  try {
    if (localStorage.getItem("cs-light-default")) return;
    localStorage.setItem("cs-light-default", "1");
    localStorage.theme = "light";
    var root = document.documentElement;
    root.classList.remove("dark"); root.classList.add("light");
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", "#ffffff");
  } catch (e) {}
})();

(function () {
  if (window.top !== window) return;                      // inside the dashboard panel
  if (window.opener || window.name === "ps-chat-signin") return; // sign-in popup; the dashboard closes it
  var allowed = function (p) { return /^\/(auth|oauth|admin)(\/|$)/.test(p); };
  var toDashboard = function () { location.replace("/"); };
  if (!allowed(location.pathname)) return toDashboard();
  var last = location.pathname;
  setInterval(function () {
    var p = location.pathname;
    if (p !== last) { last = p; if (!allowed(p)) toDashboard(); }
  }, 250);
})();

// Name shown to users is just "CraneSignal" (the sign-in popup title and heading
// otherwise read "CraneSignal (Open WebUI)"). See webui.Dockerfile for the license note.
(function () {
  var TAG = " (Open WebUI)";
  var brandFirstAccount = function () {
    // Open WebUI's first-run panel owns the button that enables the first
    // account, so it must stay functional. Replace its vendor pitch with a
    // short CraneSignal handoff and hide the vendor documentation link.
    var replacements = {
      "Open WebUI": "CraneSignal",
      "Welcome to your AI home.": "Your early-lead workspace is ready.",
      "Run AI on your own terms. Connect any model, extend with code, and protect what matters without compromise. Your models, your data, your machine, wherever you open it.":
        "Create your local account to explore sourced apartment leads, market signals, and the research assistant.",
      "Get started": "Create your account"
    };
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (var n = w.nextNode(); n; n = w.nextNode()) {
      var key = n.nodeValue.trim();
      if (Object.prototype.hasOwnProperty.call(replacements, key)) n.nodeValue = n.nodeValue.replace(key, replacements[key]);
    }
    var docs = document.querySelector('a[href^="https://docs.openwebui.com"]');
    if (docs) docs.style.display = "none";
    var start = document.querySelector('button[aria-label="Get started"]');
    if (start) start.setAttribute("aria-label", "Create your account");
  };
  var clean = function () {
    if (document.title.indexOf(TAG) >= 0) document.title = document.title.split(TAG).join("");
    if (!document.body) return;
    brandFirstAccount();
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (var n = w.nextNode(); n; n = w.nextNode()) {
      if (n.nodeValue.indexOf(TAG) >= 0) n.nodeValue = n.nodeValue.split(TAG).join("");
    }
  };
  clean();
  new MutationObserver(clean).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();
