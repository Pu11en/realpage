import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autobold import StreamBolder, bold  # noqa: E402

ANSWER = """Orchards Market Plaza is a senior community in Plano.

- Call Jane Doe at (682) 418-2225 or 469-829-7591
- Size: 178 units, sold Sep 13, 2026 (also 9/13/2026)
- Why now: lease-up ends March 3, 2027

Next: ask for the regional manager.
Sources: [CoStar sale record](https://example.com/p/469-829-7591?units=178%20units), county records"""

EXPECTED = """Orchards Market Plaza is a senior community in Plano.

- **Call** Jane Doe at **(682) 418-2225** or **469-829-7591**
- **Size:** **178 units**, sold **Sep 13, 2026** (also **9/13/2026**)
- **Why now:** lease-up ends **March 3, 2027**

**Next:** ask for the regional manager.
**Sources:** [CoStar sale record](https://example.com/p/469-829-7591?units=178%20units), county records"""


def test_plain_is_bolded():
    assert bold(ANSWER) == EXPECTED


def test_labels():
    assert bold("Software: Entrata\nAsk for: the owner") == "**Software:** Entrata\n**Ask for:** the owner"


def test_already_bold_untouched():
    text = "**Next:** call **(682) 418-2225** about **178 units** on **Sep 13, 2026**."
    assert bold(text) == text
    assert bold(EXPECTED) == EXPECTED
    assert "****" not in bold(bold(ANSWER))


def test_bold_phrase_containing_fact_untouched():
    text = "**Grand at Legacy West, 400 units** is next."
    assert bold(text) == text


def test_urls_untouched():
    for text in ("See https://x.com/call/469-829-7591/178 units",
                 "[469-829-7591](tel:469-829-7591)",
                 "<https://example.com/Sep 13, 2026>",
                 "`Next:` in code"):
        assert "**" not in bold(text), text


def test_only_stars_added():
    out = bold(ANSWER)
    assert out.replace("**", "") == ANSWER.replace("**", "")


def test_call_only_as_label():
    assert bold("You should Call them.") == "You should Call them."
    assert bold("Callahan owns it.") == "Callahan owns it."


def _stream(pieces):
    b = StreamBolder()
    return "".join(b.feed(p) for p in pieces) + b.flush()


def test_phone_split_across_two_chunks():
    assert _stream(["Ring (682) 41", "8-2225 today."]) == "Ring **(682) 418-2225** today."
    assert _stream(["Ring 469-8", "29-7591 today."]) == "Ring **469-829-7591** today."


def test_label_and_call_split_mid_line():
    assert _stream(["- Ca", "ll Jane\nNe", "xt: go"]) == "- **Call** Jane\n**Next:** go"
    # "Call" after a mid-line chunk boundary is not at a line start.
    assert _stream(["You should ", "Call them."]) == "You should Call them."


def test_existing_bold_split_across_chunks():
    assert _stream(["Call **(682) 418-", "2225** now"]) == "**Call** **(682) 418-2225** now"


def test_stream_matches_whole_for_any_split():
    rng = random.Random(7)
    for text in (ANSWER, EXPECTED):
        for _ in range(300):
            cuts = sorted(rng.sample(range(1, len(text)), rng.randint(1, 30)))
            pieces = [text[a:b] for a, b in zip([0] + cuts, cuts + [len(text)])]
            assert _stream(pieces) == bold(text)


def test_stream_holds_back_only_a_short_tail():
    b = StreamBolder()
    out = b.feed("word " * 40)
    assert len(out) >= len("word " * 40) - 40


def test_gateway_sse_rewrite():
    import json
    os.environ.setdefault("API_SERVER_KEY", "test")
    import proxy

    def chunk(delta, finish=None):
        return ("data: " + json.dumps({"id": "c1", "object": "chat.completion.chunk",
                "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}) + "\n\n").encode()

    raw = (chunk({"role": "assistant"}) + chunk({"content": "Ring (682) 41"})
           + chunk({"content": "8-2225 now. Next:"}) + chunk({}, "stop") + b"data: [DONE]\n\n")
    rw = proxy._SseBolder()
    # Feed in awkward byte pieces, splitting lines mid-way.
    out = b"".join(rw.feed(raw[i:i + 7]) for i in range(0, len(raw), 7)) + rw.close()
    assert proxy._sse_text(out) == "Ring **(682) 418-2225** now. **Next:**"
    assert out.rstrip().endswith(b"data: [DONE]")
    assert b"**Next:**" in out.split(b'"finish_reason": "stop"')[0]
