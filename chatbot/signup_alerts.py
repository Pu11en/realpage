"""Post each new CraneSignal account to the New Crane Users Discord channel; runs in the Open WebUI container.

Runs next to Open WebUI in the chat container (see webui.Dockerfile). Open
WebUI's own "user created" webhook only sends an ID, so this reads the account
straight from its database: name, email, how they signed up, and the optional
"What best describes you?" pick, which the sign-up page saves to the landing
page's signup list (business/marketing/landing/server.py).
"""
import csv, datetime, io, json, os, sqlite3, time, urllib.request, zoneinfo

DB = "/app/backend/data/webui.db"
STATE = "/app/backend/data/.signup-alerts-last"
WEBHOOK = os.environ.get("SIGNUP_WEBHOOK_URL") or os.environ.get("WEBHOOK_URL", "")
SIGNUPS = os.environ.get("LANDING_SIGNUPS_URL", "")  # https://cranesignal.com/api/signups?key=...
WAIT = 45  # seconds after sign-up, so the picker choice has arrived
CT = zoneinfo.ZoneInfo("America/Chicago")


def picks():
    if not SIGNUPS:
        return {}
    try:
        text = urllib.request.urlopen(SIGNUPS, timeout=10).read().decode("utf-8", "replace")
    except Exception:
        return {}
    return {r["email"].strip().lower(): r["role"] for r in csv.DictReader(io.StringIO(text))
            if r.get("metro") == "(app sign-up)" and r.get("role")}


def post(text):
    req = urllib.request.Request(WEBHOOK, data=json.dumps({"content": text}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "CraneSignal"})
    urllib.request.urlopen(req, timeout=10)


def message(name, email, created, google, role):
    when = datetime.datetime.fromtimestamp(created, CT).strftime("%b %d, %-I:%M %p CT")
    return "\n".join([
        "🏗️ **New CraneSignal sign-up**",
        f"**Name:** {name or '(none given)'}",
        f"**Email:** {email}",
        f"**What they are:** {role or 'Did not pick'}",
        f"**Signed up with:** {'Google' if google else 'Email and password'}",
        f"**When:** {when}",
    ])


def main():
    if not WEBHOOK:
        return
    try:
        last = int(open(STATE).read().strip())
    except Exception:
        last = int(time.time())  # first run: only people who sign up from now on
        open(STATE, "w").write(str(last))
    while True:
        try:
            db = sqlite3.connect(DB, timeout=10)
            rows = db.execute(
                "select u.id, u.name, u.email, u.created_at,"
                " (u.oauth is not null and u.oauth not in ('', 'null', '{}'))"
                "  or exists(select 1 from oauth_session s where s.user_id = u.id)"
                " from user u where u.created_at > ? and u.created_at <= ? order by u.created_at",
                (last, int(time.time()) - WAIT)).fetchall()
            db.close()
            if rows:
                roles = picks()
                for _id, name, email, created, google in rows:
                    post(message(name, email, created, google, roles.get((email or "").lower())))
                    last = created
                    open(STATE, "w").write(str(last))
        except Exception as e:
            print("signup_alerts:", e, flush=True)
        time.sleep(20)


if __name__ == "__main__":
    main()
