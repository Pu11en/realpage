"""Answer checker helper for check-answers.sh (PLAN-chat-finish T2)."""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = os.environ.get("BOT_URL", "http://localhost:18080") + "/v1/chat/completions"
HEADERS = {
    "Authorization": "Bearer " + os.environ.get("BOT_KEY", "local-trial-key-change-me"),
    "X-OpenWebUI-User-Email": "admin@localhost",
    "Content-Type": "application/json",
}
QUESTIONS = [
    "Which buildings sold recently?",
    "Which 3 leads should I call first this week?",
    "What software does Grand At Legacy West Apartments run?",
    "Who owns Ellington in Plano?",
    "Fresh deep dive on Orchards Market Plaza Senior Apts, Plano (178 units, "
    "Entrata): who runs it, and why would they switch now?",
]
MAX_WORDS = 60
MAX_DEEP_WORDS = 70  # deep dives, not counting the link row and Sources
LINK_WORDS = ["record", "news", "website"]  # must be links on the Sources line
# Our own data's "Say it as" names (query-propertystack skill) have no URL.
OWN_DATA = ["county property records", "county sales records", "building websites",
            "city permits and news", "contact info from building websites"]
CODES = ["SWDNL", "WDNL", "hop-portal", "no-portal-link", "apt_id", "score_"]
FILES = [".csv]", ".csv", ".md]"]
SCRIPT = ["opener", "objection"]


def ask(question):
    body = json.dumps({
        "model": "hermes-agent",
        "stream": False,
        "messages": [{"role": "user", "content": question}],
    }).encode()
    req = urllib.request.Request(URL, data=body, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=170) as resp:
        return json.load(resp)["choices"][0]["message"]["content"] or ""


SOURCES_RE = re.compile(r"\s*\**\s*Sources\s*:", re.I)
LINK_ROW_RE = re.compile(r"\s*(🗺|📄|📰|🌐)")


def is_deep_dive(question):
    return "deep dive" in question.lower()


def word_count(answer):
    kept = [ln for ln in answer.splitlines()
            if not SOURCES_RE.match(ln) and not LINK_ROW_RE.match(ln)]
    text = re.sub(r"\]\([^)]*\)", "]", "\n".join(kept))  # link URLs aren't words
    return len(re.findall(r"[A-Za-z0-9][\w'’.,/-]*", text))


def unlinked_sources(answer):
    """Words like "record"/"news"/"website" on the Sources line that aren't links."""
    out = []
    for ln in answer.splitlines():
        if SOURCES_RE.match(ln):
            plain = re.sub(r"\[[^\]]*\]\([^)]*\)", "", ln).lower()
            for name in OWN_DATA:
                plain = plain.replace(name, "")
            out += [w for w in LINK_WORDS if w in plain]
    return out


def problems(answer, question=""):
    out = []
    n = word_count(answer)
    limit = MAX_DEEP_WORDS if is_deep_dive(question) else MAX_WORDS
    if n > limit:
        out.append(f"{n} words (max {limit})")
    if is_deep_dive(question) and "](http" not in answer:
        out.append("deep dive has no link")
    out += [f"Sources names {w!r} without a link" for w in unlinked_sources(answer)]
    out += [f"raw code {c!r}" for c in CODES if c in answer]
    out += [f"file name {f!r}" for f in FILES if f in answer]
    low = answer.lower()
    out += [f"call script word {s!r}" for s in SCRIPT if s in low]
    if "**" not in answer:
        out.append("no bold")
    return out


def main():
    try:
        urllib.request.urlopen(urllib.request.Request(
            URL.replace("/chat/completions", "/models"), headers=HEADERS), timeout=5)
    except (urllib.error.URLError, OSError) as e:
        print(f"The bot is not up at {URL} ({e}).")
        print("Start the local stack first: bash tooling/dev.sh")
        return 2

    with ThreadPoolExecutor(len(QUESTIONS)) as pool:
        futures = [pool.submit(ask, q) for q in QUESTIONS]
        results = []
        for q, f in zip(QUESTIONS, futures):
            try:
                results.append((q, f.result(), None))
            except Exception as e:  # noqa: BLE001
                results.append((q, "", f"error: {e}"))

    failed = 0
    for q, answer, err in results:
        bad = [err] if err else problems(answer, q)
        failed += bool(bad)
        print("=" * 70)
        print(("FAIL" if bad else "PASS") + f" [{word_count(answer)} words] {q}")
        for b in bad:
            print("  -", b)
        print("-" * 70)
        print(answer.strip())
    print("=" * 70)
    print(f"check-answers: {len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
