"""Clean the links in an answer before it leaves the proxy.

- Link guard: a markdown link whose URL no tool ever returned (see the
  propertystack plugin's seen-URLs file) is removed completely, with its
  emoji / " · " separator / "( )" wrapper. Google Maps search links are
  always allowed (they are built from the address).
- Labels: every link outside the deep-dive link row is named after where it
  really goes ("Community Impact", "Texas building record", ...), so the AI
  can't mislabel a council video as a "County sales record".
- The link row's 📄 Permit is never a meeting video: such a link is dropped.
- Deep dives: the **Sources:** line is dropped (the link row covers it).
- In-chat "#ask:" links (e.g. [🔍 Find contact](#ask:Deep dive on ...)) are
  not web links: they are left untouched (only http(s) links are checked).

fix_links(text, seen) works on whole text; LineFixer does the same for a
stream, releasing text one finished line at a time.
"""
import os
import re
from urllib.parse import urlsplit

HERMES_HOME = os.environ.get("HERMES_HOME", "/opt/data")
SEEN_FILE = os.path.join(HERMES_HOME, "seen-urls.txt")

_LINK_RE = re.compile(r"\[([^\]\n]*)\]\((https?://[^)\s]+)\)")
_ROW_EMOJI = ("🗺️", "🗺", "📄", "📰", "🌐")
_ROW_LABELS = {"map", "permit", "news", "website"}
_VIDEO_RE = re.compile(r"swagit\.com|youtube\.com|youtu\.be|vimeo\.com|granicus\.com/player|/videos?/", re.I)
_SOURCES_RE = re.compile(r"^\s*\**\s*Sources\s*:?", re.I)

# Only used when link cleaning leaves nothing to show.
EMPTY_REPLY = """**I don't have that.**
**Next:** Ask about a Texas building or RealPage."""

_SITE_LABELS = [
    (r"(^|\.)tdlr\.texas\.gov$", "Texas building record"),
    (r"(^|\.)data\.texas\.gov$", "Texas county records"),
    (r"(^|\.)communityimpact\.com$", "Community Impact"),
    (r"(^|\.)dallasnews\.com$", "Dallas Morning News"),
    (r"(^|\.)bizjournals\.com$", "Business Journal"),
    (r"(^|\.)candysdirt\.com$", "CandysDirt"),
    (r"(^|\.)therealdeal\.com$", "The Real Deal"),
    (r"(^|\.)zabalist\.com$", "Texas building record"),
    (r"(^|\.)(loftliving|activebuilding|securecafe|rentcafe|residentportal|prospectportal|"
     r"entrata|yardi|appfolio|yottareal|myresman)\.com$|realpage\.com$", "Software proof"),
]


def _norm(url: str) -> str:
    url = url.strip().rstrip(".,;:!?'\"")
    try:
        p = urlsplit(url)
    except ValueError:
        return url
    path = p.path.rstrip("/")
    return f"{p.netloc.lower().removeprefix('www.')}{path}{'?' + p.query if p.query else ''}"


def load_seen(path: str = SEEN_FILE) -> set[str]:
    try:
        with open(path, encoding="utf-8") as f:
            return {_norm(line) for line in f if line.strip()}
    except OSError:
        return set()


def _is_maps(url: str) -> bool:
    p = urlsplit(url)
    return p.netloc.lower().endswith("google.com") and p.path.startswith("/maps")


# CraneSignal's own "how it was built and tested" page: the readable source for
# questions about CraneSignal itself, so it is always allowed.
HOOD_URL = "https://app.cranesignal.com/under-the-hood.html"


def _is_hood(url: str) -> bool:
    return _norm(url) == _norm(HOOD_URL)


def label_for(url: str) -> str:
    host = urlsplit(url).netloc.lower().removeprefix("www.")
    if _is_maps(url):
        return "Map"
    if _is_hood(url):
        return "Under the Hood"
    if host.endswith("swagit.com"):
        city = host.split(".")[0].removesuffix("tx").title()
        return f"{city} city video"
    if host.endswith("legistar.com") or host.endswith("civicplus.com"):
        city = host.split(".")[0].title()
        return f"{city} city agenda" if city not in ("Webapi", "Content") else "City agenda"
    for rx, name in _SITE_LABELS:
        if re.search(rx, host):
            return name
    return host


def _drop_span(line: str, start: int, end: int) -> str:
    """Remove line[start:end] plus its wrapper: '( ... )', an emoji and one ' · '."""
    before, after = line[:start], line[end:]
    if before.rstrip().endswith("(") and after.lstrip().startswith(")"):
        before, after = before.rstrip()[:-1], after.lstrip()[1:]
    stripped = before.rstrip()
    for e in _ROW_EMOJI:
        if stripped.endswith(e):
            before = stripped[: -len(e)]
            break
    b, a = before.rstrip(), after.lstrip()
    if a.startswith("·"):
        a = a[1:].lstrip()
        return (b + " " + a) if b else a
    if b.endswith("·"):
        b = b[:-1].rstrip()
        return b + (" " + a if a else "")
    return (b + " " + a).strip() if b and a else (b or a)


def _fix_line(line: str, seen: set[str], deep_dive: bool) -> str | None:
    if deep_dive and _SOURCES_RE.match(line):
        return None
    while True:
        changed = False
        for m in _LINK_RE.finditer(line):
            label, url = m.group(1), m.group(2)
            in_row = label.strip().lower() in _ROW_LABELS and line[: m.start()].rstrip().endswith(_ROW_EMOJI)
            bad = not _is_maps(url) and not _is_hood(url) and _norm(url) not in seen
            if in_row and label.strip().lower() == "permit" and _VIDEO_RE.search(url):
                bad = True
            if bad:
                line = _drop_span(line, m.start(), m.end())
                changed = True
                break
            if not in_row:
                new = label_for(url)
                if new != label:
                    line = line[: m.start()] + f"[{new}]({url})" + line[m.end():]
                    changed = True
                    break
        if not changed:
            break
    # A Sources line left with nothing to cite goes; a bare link row too.
    if _SOURCES_RE.match(line) and not re.sub(r"[\s*·:,;()]|Sources", "", line, flags=re.I):
        return None
    if line.strip() and not re.sub(r"[\s·🗺️🗺📄📰🌐️]", "", line):
        return None
    return line


def fix_links(text: str, seen: set[str] | None = None, deep_dive: bool = False) -> str:
    seen = load_seen() if seen is None else seen
    out = []
    for line in text.split("\n"):
        fixed = _fix_line(line, seen, deep_dive)
        if fixed is not None:
            out.append(fixed)
    return "\n".join(out)


def finalize_answer(text: str, seen: set[str] | None = None, deep_dive: bool = False) -> str:
    """Last step before an answer leaves the proxy.

    Fake links (never returned by a tool) are removed; the answer itself is
    kept. A link is not required -- facts from our own data or general
    knowledge name their source in words (see SOUL.md). ``seen`` is
    injectable so this is tested offline.
    """
    seen = load_seen() if seen is None else seen
    cleaned = fix_links(text, seen, deep_dive=deep_dive).strip()
    return cleaned or EMPTY_REPLY


class LineFixer:
    """fix_links for a stream: hold text until its line is complete."""

    def __init__(self, seen: set[str] | None = None, deep_dive: bool = False) -> None:
        self.seen = load_seen() if seen is None else seen
        self.deep_dive = deep_dive
        self.buf = ""

    def feed(self, text: str) -> str:
        self.buf += text
        if "\n" not in self.buf:
            return ""
        done, self.buf = self.buf.rsplit("\n", 1)
        out = []
        for line in done.split("\n"):
            fixed = _fix_line(line, self.seen, self.deep_dive)
            if fixed is not None:
                out.append(fixed + "\n")
        return "".join(out)

    def flush(self) -> str:
        rest, self.buf = self.buf, ""
        if not rest:
            return ""
        fixed = _fix_line(rest, self.seen, self.deep_dive)
        return fixed or ""
