"""Lawsuit data for one AI Visibility run: every answer that raises the antitrust case.

For each answer that mentions the antitrust case / DOJ / settlement / price-fixing we keep the exact
sentence(s), the AI, the question and (for gemini-web) the websites Gemini quoted. Each mention gets a
tone: harsh, neutral or settled ("it's settled now"). Real runs ask Gemini for the tone (one call per
mention); practice runs, the Sept 12 baseline and any failed call use a simple word list instead.
The websites become a leaderboard with the change vs the previous run and a flag for realpage.com.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

CASE_RE = re.compile(r"antitrust|\bDOJ\b|Department of Justice|lawsuit|collusion|price[- ]fixing|"
                     r"rent[- ]fixing|cartel|settle(?:d|ment)|sued|attorneys? general", re.I)
SETTLED_RE = re.compile(r"settle(?:d|ment|s)|consent decree|resolved|agreed to|dismiss(?:ed|al)", re.I)
HARSH_RE = re.compile(r"price[- ]fixing|rent[- ]fixing|collu(?:de|sion)|cartel|illegal|alleg|accus|"
                      r"scheme|inflat|conspir|unlawful|gouging", re.I)
TONES = ("harsh", "neutral", "settled")
TONE_PROMPT = ("Below is what an AI assistant said about RealPage and its antitrust case. Label its tone:\n"
               "- harsh: it stresses wrongdoing (price-fixing, collusion, harm to renters)\n"
               "- settled: it presents the case as over or resolved (a settlement, agreement, dismissal)\n"
               "- neutral: it states the case matter-of-factly without either\n"
               'Reply ONLY with JSON like {"tone": "neutral"}.\n\nText: ')


def sentences(text: str) -> list[str]:
    text = re.sub(r"[*_#>`]+", "", text or "")
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [" ".join(p.split()) for p in parts if p.strip()]


def case_sentences(text: str) -> list[str]:
    return [s for s in sentences(text) if CASE_RE.search(s)]


def word_tone(text: str) -> str:
    if SETTLED_RE.search(text):
        return "settled"
    return "harsh" if HARSH_RE.search(text) else "neutral"


def gemini_tone(text: str) -> str:
    """One real Gemini call (throttled by local_ai); raises on any problem so the caller falls back."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tooling" / "ai-visibility"))
    import local_ai
    reply = local_ai.ask_gemini("gemini", TONE_PROMPT + text, want_json=True)
    tone = str(json.loads(local_ai._json_only(reply)).get("tone", "")).strip().lower()
    if tone not in TONES:
        raise ValueError(f"unexpected tone {tone!r}")
    return tone


def label_tone(text: str, ask=None) -> tuple[str, str]:
    """(tone, how): how is "gemini" when the AI labelled it, "words" for the word-list fallback."""
    if ask:
        try:
            return ask(text), "gemini"
        except Exception as exc:  # noqa: BLE001 -- rate limit, bad JSON, no key: fall back
            print(f"[lawsuit] tone call failed, using word list: {str(exc)[:120]}", file=sys.stderr)
    return word_tone(text), "words"


def website(source: dict) -> str:
    """Gemini's grounding links are Google redirects; the title holds the website name."""
    title = (source.get("title") or "").strip().lower()
    if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", title):
        return title.removeprefix("www.")
    host = urlparse(source.get("url") or "").hostname or ""
    return (host.removeprefix("www.") if host and "vertexaisearch" not in host else title) or "unknown"


def load_sources(run_dir: Path | None) -> list[dict]:
    path = run_dir and run_dir / "gemini-sources.jsonl"
    if not path or not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _sources_for(question: str, answer: str, lines: list[dict]) -> list[dict]:
    answer = answer.strip()
    hit = next((l for l in lines if l.get("answer", "").strip() == answer), None)
    hit = hit or next((l for l in lines if question and question in l.get("prompt", "")), None)
    seen, out = set(), []
    for s in (hit or {}).get("sources", []):
        site = website(s)
        if site not in seen:
            seen.add(site)
            out.append({"site": site, "title": s.get("title", ""), "url": s.get("url", "")})
    return out


def mentions(report: dict, run_dir: Path | None = None, ask=None, names=None) -> list[dict]:
    lines = load_sources(run_dir)
    out = []
    for run in report["audit"]["runs"]:
        answer = (run.get("result") or {}).get("text") or ""
        found = case_sentences(answer)
        if not found:
            continue
        quote = " ".join(found)
        tone, how = label_tone(quote, ask)
        model = run["model"]
        out.append({
            "model": model,
            "name": (names or {}).get(model, model),
            "question": run["prompt"]["text"],
            "namesBrand": bool(run["prompt"].get("targetIncluded")),
            "sentences": found,
            "tone": tone,
            "toneBy": how,
            "sources": _sources_for(run["prompt"]["text"], answer, lines) if model.endswith("-web") else [],
        })
    return out


def tone_mix(found: list[dict]) -> dict:
    mix: dict[str, dict] = {}
    for m in found:
        mix.setdefault(m["model"], dict.fromkeys(TONES, 0))[m["tone"]] += 1
    return mix


def leaderboard(found: list[dict], previous: list[dict] | None = None, target_domain: str = "realpage.com") -> list[dict]:
    """Websites quoted when the case comes up: mentions citing each one, and the change vs last run."""
    counts: dict[str, int] = {}
    for m in found:
        for s in m["sources"]:
            counts[s["site"]] = counts.get(s["site"], 0) + 1
    before = {row["site"]: row["count"] for row in previous or []}
    rows = [{"site": site, "count": counts.get(site, 0), "previous": before.get(site, 0) if previous is not None else None}
            for site in set(counts) | {s for s, c in before.items() if c}]
    for r in rows:
        r["change"] = None if r["previous"] is None else r["count"] - r["previous"]
        r["isTarget"] = r["site"] == target_domain or r["site"].endswith("." + target_domain)
    return sorted(rows, key=lambda r: (-r["count"], -(r["previous"] or 0), r["site"]))


def lawsuit_data(report: dict, run_dir: Path | None = None, ask=None, previous: dict | None = None,
                 names=None) -> dict:
    """Everything the lawsuit section needs for one run; previous is the last run's history entry."""
    found = mentions(report, run_dir, ask, names)
    domain = report["audit"]["target"].get("domain") or "realpage.com"
    before = (previous or {}).get("lawsuit")
    return {
        "mentions": found,
        "toneMix": tone_mix(found),
        "sources": leaderboard(found, before["sources"] if before else None, domain),
        "comparedWith": previous["date"] if before else None,
    }
