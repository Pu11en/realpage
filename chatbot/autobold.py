"""Bold the key facts the bot left plain (phones, unit counts, dates, labels).

bold(text) is idempotent: text already inside **...**, links, URLs and `code`
is never touched, and nothing but the added ** changes. StreamBolder does the
same for text arriving in pieces, holding back only a short tail so a pattern
split across two chunks is still caught.
"""
import re

_MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
          r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
_FACT_RE = re.compile(
    r"\(\d{3}\)\s?\d{3}-\d{4}(?!\d)"                    # (682) 418-2225
    r"|(?<![\w/.-])\d{3}[-.]\d{3}[-.]\d{4}(?![\w-])"     # 469-829-7591
    r"|(?<![\w,.])\d[\d,]*\s+units\b"                   # 178 units
    rf"|\b{_MONTH}\.?\s+\d{{1,2}},?\s+\d{{4}}(?!\d)"    # Sep 13, 2026
    r"|(?<![\w/])\d{1,2}/\d{1,2}/\d{2,4}(?![\d/])"      # 9/13/2026
    r"|\b(?:Next|Sources|Why now|Size|Software|Ask for):"
)
# "Call" is a label only at the start of a line or bullet.
_CALL_RE = re.compile(r"(?m)(?:^|(?<=^[-*] )|(?<=^  [-*] ))Call\b")

# Spans never edited: existing bold, links, bare URLs, inline code.
_PROTECT_RE = re.compile(
    r"\*\*[^\n]*?\*\*"
    r"|!?\[[^\]\n]*\]\([^)\s]*\)"
    r"|<?https?://[^\s)>\]]+>?"
    r"|\bwww\.[^\s)>\]]+"
    r"|`[^`\n]*`"
)
# How many characters a stream holds back (longest pattern is ~20).
HOLD = 40


def _spans(text: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Return (protected spans, fact spans outside them), both sorted."""
    protected = [m.span() for m in _PROTECT_RE.finditer(text)]
    facts = []
    for rx in (_FACT_RE, _CALL_RE):
        for m in rx.finditer(text):
            s, e = m.span()
            if not any(ps < e and s < pe for ps, pe in protected):
                facts.append((s, e))
    facts.sort()
    return protected, facts


def bold(text: str, before: str = "") -> str:
    """Bold plain facts in text. `before` is text already sent on the same
    line (used only as context, never returned)."""
    if not text:
        return text
    _, facts = _spans(before + text)
    out, pos = [], 0
    for s, e in facts:
        s, e = s - len(before), e - len(before)
        if s < pos:
            continue
        out.append(text[pos:s])
        out.append(f"**{text[s:e]}**")
        pos = e
    out.append(text[pos:])
    return "".join(out)


def _safe_cut(buf: str) -> int:
    """Largest index where buf can be split without breaking a pattern or span."""
    cut = max(0, len(buf) - HOLD)
    # Never split inside a line's open ** / [ / ` (they close later on the line).
    line_start = buf.rfind("\n", 0, cut) + 1
    head = buf[line_start:cut]
    for opener in ("**", "`"):
        if head.count(opener) % 2:
            cut = min(cut, line_start + head.rfind(opener))
    open_link = head.rfind("[")
    if open_link > head.rfind(")"):
        cut = min(cut, line_start + open_link)
    protected, facts = _spans(buf)
    moved = True
    while moved:
        moved = False
        for s, e in protected + facts:
            if s < cut < e or (s < cut and e == len(buf)):
                cut, moved = s, True
    return cut


class StreamBolder:
    def __init__(self) -> None:
        self.buf = ""
        self.line = ""  # raw text already sent on the current line

    def _emit(self, ready: str) -> str:
        out = bold(ready, self.line)
        self.line = (self.line + ready).rsplit("\n", 1)[-1]
        return out

    def feed(self, text: str) -> str:
        self.buf += text
        cut = _safe_cut(self.line + self.buf) - len(self.line)
        if cut <= 0:
            return ""
        ready, self.buf = self.buf[:cut], self.buf[cut:]
        return self._emit(ready)

    def flush(self) -> str:
        ready, self.buf = self.buf, ""
        return self._emit(ready)

    def reset(self) -> None:
        self.buf = self.line = ""
