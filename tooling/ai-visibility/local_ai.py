"""OpenAI-style server that answers with local AI sessions instead of a paid API.

    python3 tooling/ai-visibility/local_ai.py <port>

Model names NiubiGEO can ask for:
  claude      Claude (Sonnet) from its own memory, no web
  claude-web  Claude (Sonnet) allowed to search the web first
  chatgpt     OpenAI's model via the Codex CLI, from its own memory
Each call runs a fresh `claude -p` / `codex exec` with none of Drew's own
instructions loaded, so the answer is what a member of the public would get.
"""

from __future__ import annotations

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

PUBLIC = ("You are a helpful AI assistant chatting with a member of the public. "
          "Answer the question directly and naturally, as a chat assistant would.")
CLEAN_DIR = Path(tempfile.gettempdir()) / "ai-visibility-clean"
CODEX_HOME = CLEAN_DIR / "codex-home"
TIMEOUT = 280


def _clean_env() -> dict:
    CODEX_HOME.mkdir(parents=True, exist_ok=True)
    auth = Path.home() / ".codex" / "auth.json"
    if auth.exists() and not (CODEX_HOME / "auth.json").exists():
        shutil.copy(auth, CODEX_HOME / "auth.json")
    env = dict(os.environ, CODEX_HOME=str(CODEX_HOME))
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
        env.pop(key, None)  # use the logged-in subscriptions, never API credit
    return env


def ask(model: str, prompt: str) -> str:
    env = _clean_env()
    if model.startswith("claude"):
        tools = "WebSearch,WebFetch" if model == "claude-web" else ""
        cmd = ["claude", "-p", "--model", "sonnet", "--setting-sources", "",
               "--system-prompt", PUBLIC, "--tools", tools]
        if tools:
            cmd += ["--allowedTools", tools]
        out = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                             timeout=TIMEOUT, cwd=CLEAN_DIR, env=env)
        text = out.stdout.strip()
    elif model == "chatgpt":
        last = CLEAN_DIR / f"codex-{uuid.uuid4().hex}.txt"
        out = subprocess.run(["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only",
                              "-o", str(last), "-"], input=f"{PUBLIC}\n\n{prompt}",
                             capture_output=True, text=True, timeout=TIMEOUT, cwd=CLEAN_DIR, env=env)
        text = last.read_text().strip() if last.exists() else ""
        last.unlink(missing_ok=True)
    else:
        raise ValueError(f"unknown model {model}")
    if not text:
        raise RuntimeError(f"{model} gave no answer: {out.stderr[-300:]}")
    return text


def _json_only(text: str) -> str:
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    end = max(text.rfind("}"), text.rfind("]"))
    return text[start:end + 1] if start >= 0 and end > start else text


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # model list
        self._send(200, {"data": [{"id": m} for m in ("claude", "claude-web", "chatgpt")]})

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
        prompt = "\n\n".join(str(m.get("content", "")) for m in req.get("messages", []))
        tool = next((t["function"] for t in req.get("tools", []) if t.get("type") == "function"), None)
        if tool:
            prompt += ("\n\nReturn ONLY a JSON object (no markdown) matching this JSON schema:\n"
                       + json.dumps(tool.get("parameters", {})))
        try:
            text = ask(req.get("model", ""), prompt)
        except Exception as exc:  # noqa: BLE001 -- report to NiubiGEO as a failed call
            print(f"[local_ai] {req.get('model')}: {exc}", file=sys.stderr, flush=True)
            return self._send(502, {"error": {"message": str(exc)[:500]}})
        message = {"role": "assistant", "content": text}
        if tool:
            message["content"] = None
            message["tool_calls"] = [{"id": "call_1", "type": "function",
                                      "function": {"name": tool["name"], "arguments": _json_only(text)}}]
        print(f"[local_ai] {req.get('model')}: answered ({len(text)} chars)", file=sys.stderr, flush=True)
        self._send(200, {"id": uuid.uuid4().hex, "object": "chat.completion", "model": req.get("model"),
                         "choices": [{"index": 0, "message": message,
                                      "finish_reason": "tool_calls" if tool else "stop"}],
                         "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(text) // 4,
                                   "total_tokens": (len(prompt) + len(text)) // 4}})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
