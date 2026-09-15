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
