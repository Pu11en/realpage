"""B1: nothing a chat user can see says PropertyStack, Hermes or Open WebUI."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHAT = ROOT / "chatbot"
PLUGIN = CHAT / "hermes-profile/plugins/propertystack/__init__.py"
SKILL = CHAT / "hermes-profile/skills/query-propertystack/SKILL.md"
BAD = re.compile(r"PropertyStack|Hermes|Open WebUI", re.I)


def _source_names():
    tree = ast.parse(PLUGIN.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "SOURCE_NAMES":
            return ast.literal_eval(node.value)
    raise AssertionError("SOURCE_NAMES not found")


def test_source_labels_say_cranesignal():
    names = _source_names()
    assert names["leads"] == names["state_leads"] == "CraneSignal lead ranking"
    assert not [v for v in names.values() if BAD.search(v)]


def test_tool_descriptions_clean():
    # Tool descriptions and schema text are what the agent reads and may repeat.
    text = PLUGIN.read_text()
    shown = re.findall(r'description="([^"]*)"', text) + re.findall(r'_schema\("\w+", "([^"]*)"', text)
    shown += re.findall(r'^\s+"([^"]*(?:tables|SELECT)[^"]*)",?$', text, re.M)
    assert shown and not [s for s in shown if BAD.search(s)]


def test_skill_sources_column_clean():
    rows = [l for l in SKILL.read_text().splitlines() if l.startswith("| `")]
    say = [l.split("|")[2] for l in rows if l.count("|") >= 4]
    assert say and not [s for s in say if BAD.search(s)]
    desc = re.search(r'^description: "(.*)"$', SKILL.read_text(), re.M).group(1)
    assert not BAD.search(desc)


def test_proxy_user_messages_clean():
    # Strings the proxy sends back to people: errors and limit messages.
    tree = ast.parse((CHAT / "proxy.py").read_text())
    msgs = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and " " in n.value and not n.value.startswith(("http", "X-", "Bearer"))]
    doc = ast.get_docstring(tree) or ""
    user = [m for m in msgs if m != doc and not m.startswith(("Public chat", "Validate", "Answer from", "Open WebUI's"))
            and "\n" not in m]
    assert not [m for m in user if BAD.search(m)], [m for m in user if BAD.search(m)]


def test_signin_title_is_just_cranesignal():
    assert "WEBUI_NAME: CraneSignal" in (CHAT / "docker-compose.local.yml").read_text()
    assert "(Open WebUI)'$/    pass/" in (CHAT / "webui.Dockerfile").read_text()
    js = (CHAT / "branding/loader.js").read_text()
    assert '" (Open WebUI)"' in js and "document.title" in js
