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


def word_count(answer):
    kept = [ln for ln in answer.splitlines()
            if not re.match(r"\s*\**\s*Sources\s*:", ln, re.I)]
    text = re.sub(r"\]\([^)]*\)", "]", "\n".join(kept))  # link URLs aren't words
    return len(re.findall(r"[A-Za-z0-9][\w'’.,/-]*", text))


def problems(answer):
    out = []
    n = word_count(answer)
    if n > MAX_WORDS:
        out.append(f"{n} words (max {MAX_WORDS})")
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
        bad = [err] if err else problems(answer)
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
