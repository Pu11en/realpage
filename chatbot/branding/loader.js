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
  var toDashboard = function () { location.replace("/map.html"); };
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
      "Get started": "Create your account",
      "Create Account": "Create account"
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
  // Sign-in page: friendlier placeholders and a link back to the home page.
  var brandAuth = function () {
    if (!/^\/auth(\/|$)/.test(location.pathname)) return;
    var ph = { "Enter Your Email": "you@company.com", "Enter Your Password": "Your password",
               "Enter Your Full Name": "Your name" };
    document.querySelectorAll("input[placeholder]").forEach(function (i) {
      if (ph[i.placeholder]) i.placeholder = ph[i.placeholder];
    });
    if (window.top === window && !window.opener && !document.querySelector(".cs-auth-home")) {
      var a = document.createElement("a");
      a.className = "cs-auth-home";
      a.href = location.port === "8876" ? "http://localhost:8765" : "https://cranesignal.com";
      a.textContent = "\u2190 Back to home page";
      document.body.appendChild(a);
    }
  };
  // Sign-up only: an optional "What best describes you?" picker. Nothing is
  // required; if they pick one, it is sent with their email to the landing
  // page's signup list (business/marketing/landing/server.py) when they submit.
  var ROLES = ["Vendor", "Property manager", "Investor", "Lender", "Broker", "Apartment locator", "Something else"];
  var picked = "";
  var LANDING = location.port === "8876" ? "http://localhost:8765" : "https://cranesignal.com";
  var brandRolePicker = function () {
    if (!/^\/auth(\/|$)/.test(location.pathname)) return;
    var form = document.querySelector("#auth-login-card form");
    var old = document.querySelector(".cs-role");
    if (!form || !form.querySelector("input#name")) { if (old) old.remove(); return; }
    if (old) return;
    var submit = form.querySelector("button[type='submit']");
    if (!submit) return;
    var box = document.createElement("fieldset");
    box.className = "cs-role";
    box.innerHTML = '<legend>What best describes you? <span>Optional</span></legend>';
    ROLES.forEach(function (r) {
      var b = document.createElement("button");
      b.type = "button"; b.textContent = r;
      b.setAttribute("aria-pressed", r === picked ? "true" : "false");
      b.addEventListener("click", function () {
        picked = picked === r ? "" : r;
        box.querySelectorAll("button").forEach(function (x) {
          x.setAttribute("aria-pressed", x.textContent === picked ? "true" : "false");
        });
      });
      box.appendChild(b);
    });
    submit.parentElement.parentElement.insertBefore(box, submit.parentElement);
    // Google sign-ups skip the form; remember the pick so the dashboard can
    // send it once they land there signed in (site/js/app.js).
    var google = form.parentElement && form.parentElement.querySelector(".space-y-2 > button");
    if (google) google.addEventListener("click", function () {
      try { if (picked) localStorage.setItem("cs-pending-role", picked); } catch (e) {}
    }, true);
    form.addEventListener("submit", function () {
      var email = (form.querySelector("input#email") || {}).value || "";
      if (!picked || !email) return;
      try {
        fetch(LANDING + "/api/signup", { method: "POST", mode: "no-cors", keepalive: true,
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: "source=app&role=" + encodeURIComponent(picked) + "&email=" + encodeURIComponent(email) });
      } catch (e) {}
    });
  };
  var clean = function () {
    if (document.title.indexOf(TAG) >= 0) document.title = document.title.split(TAG).join("");
    if (!document.body) return;
    brandFirstAccount();
    brandAuth();
    brandRolePicker();
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (var n = w.nextNode(); n; n = w.nextNode()) {
      if (n.nodeValue.indexOf(TAG) >= 0) n.nodeValue = n.nodeValue.split(TAG).join("");
    }
  };
  clean();
  new MutationObserver(clean).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();
