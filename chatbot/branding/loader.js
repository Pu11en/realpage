// CraneSignal: the chat app only lives inside the dashboard's side panel.
// Open WebUI loads /static/loader.js on every page. If one of its pages is opened
// on its own (not framed, not the sign-in popup), send the visitor to the dashboard.
// /auth stays usable on its own for signing in; once it moves on to the chat home,
// we go to the dashboard instead. /admin stays open for the owner.
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
