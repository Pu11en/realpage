import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from linkfix import LineFixer, _norm, fix_links, label_for  # noqa: E402

TDLR = "https://www.tdlr.texas.gov/TABS/Search/Print/TABS2025020938"
NEWS = "https://communityimpact.com/richardson/housing-real-estate/sherman-street/"
VIDEO = "https://richardsontx.new.swagit.com/videos/256900"
MAPS = "https://www.google.com/maps/search/?api=1&query=1001+S+Sherman+St%2C+Richardson%2C+TX"
FAKE = "https://example.com/made-up"
SEEN = {_norm(u) for u in (TDLR, NEWS, VIDEO)}

DIVE = f"""**Call Sammy Jibrin at (214) 215-1186.** ([TDLR owner record]({TDLR}))
- **📍 Address:** 1001 S. Sherman St., Richardson
🗺️ [Map]({MAPS}) · 📄 [Permit]({VIDEO}) · 📰 [News]({NEWS}) · 🌐 [Website]({FAKE})
**Sources:** [County sales record]({VIDEO}) · [News]({NEWS})"""


def test_seen_link_kept_and_relabeled():
    out = fix_links(DIVE, SEEN, deep_dive=True)
    assert f"([Texas building record]({TDLR}))" in out
    assert f"📰 [News]({NEWS})" in out


def test_unseen_link_removed_with_its_label():
    out = fix_links(DIVE, SEEN, deep_dive=True)
    assert FAKE not in out and "Website" not in out and "🌐" not in out
    assert not out.rstrip().endswith("·")


def test_maps_link_always_kept():
    assert f"[Map]({MAPS})" in fix_links(DIVE, set(), deep_dive=True)


def test_permit_video_dropped():
    out = fix_links(DIVE, SEEN, deep_dive=True)
    assert "Permit" not in out and "📄" not in out
    assert "🗺️ [Map]" in out and " · 📰 [News]" in out


def test_deep_dive_drops_sources_line():
    assert "Sources" not in fix_links(DIVE, SEEN, deep_dive=True)


def test_normal_answer_sources_relabeled():
    text = f"**Two sold.**\n**Sources:** [County sales record]({VIDEO}) · [News]({NEWS})"
    out = fix_links(text, SEEN)
    assert f"[Richardson city video]({VIDEO})" in out
    assert f"[Community Impact]({NEWS})" in out


def test_sources_with_only_fake_links_removed():
    out = fix_links(f"**Answer.**\n**Sources:** [News]({FAKE})", SEEN)
    assert "Sources" not in out and "**Answer.**" in out


def test_plain_text_untouched():
    text = "**Grand At Legacy West runs Yardi.**\n- **Proof**: its resident login page\n**Sources:** Software check"
    assert fix_links(text, SEEN) == text


def test_stream_link_split_across_chunks():
    f = LineFixer(SEEN, deep_dive=True)
    out, step = "", 7
    for i in range(0, len(DIVE), step):
        out += f.feed(DIVE[i:i + step])
    out += f.flush()
    assert out.rstrip("\n") == fix_links(DIVE, SEEN, deep_dive=True)


def test_labels():
    assert label_for(TDLR) == "Texas building record"
    assert label_for("https://property.onesite.realpage.com/x") == "Software proof"
    assert label_for("https://orchardsmarketplaza.com/") == "orchardsmarketplaza.com"


def test_under_the_hood_link_is_an_approved_source():
    from linkfix import finalize_answer
    text = ("**Tested on 100 fixed questions; 92 passed.**\n"
            "**Next:** Open the page.\n"
            "**Sources:** [Under the Hood](https://app.cranesignal.com/under-the-hood.html)")
    out = finalize_answer(text, seen=set())
    assert "couldn't verify" not in out
    assert "under-the-hood.html" in out
