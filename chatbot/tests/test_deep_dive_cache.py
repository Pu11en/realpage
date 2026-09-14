"""Saved deep dives through the Open WebUI gateway, against a fake Hermes."""
import asyncio
import os
import sys
import tempfile

os.environ.setdefault("API_SERVER_KEY", "test-key")
os.environ.setdefault("HERMES_HOME", tempfile.mkdtemp())
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aiohttp import web  # noqa: E402
from aiohttp.test_utils import TestClient, TestServer  # noqa: E402

import proxy  # noqa: E402

QUESTION = "Deep dive on Orchards Market Plaza Senior Apts, Plano (178 units, Entrata)"


def run(case):
    async def go():
        calls = []

        async def hermes(request):
            calls.append(await request.json())
            return web.json_response({"choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": f"research #{len(calls)}"}}]})

        fake = TestServer(web.Application())
        fake.app.router.add_post("/v1/chat/completions", hermes)
        await fake.start_server()
        app = web.Application()
        app.router.add_post("/v1/chat/completions", proxy.gateway_chat)
        client = TestClient(TestServer(app))
        await client.start_server()
        proxy.HERMES_URL = str(fake.make_url("/v1/chat/completions"))
        proxy.DEEP_DIVE_DIR = tempfile.mkdtemp()
        proxy._dive_chats.clear()

        async def ask(text, chat_id):
            r = await client.post("/v1/chat/completions", json={
                "model": "hermes-agent", "messages": [{"role": "user", "content": text}]},
                headers={"Authorization": f"Bearer {proxy.HERMES_KEY}", "X-OpenWebUI-Chat-Id": chat_id})
            return (await r.json())["choices"][0]["message"]["content"]

        try:
            await case(ask, calls)
        finally:
            await client.close()
            await fake.close()

    asyncio.run(go())


def test_first_ask_saves_and_new_chat_replays():
    async def case(ask, calls):
        assert await ask(QUESTION, "chat-a") == "research #1"
        assert proxy._deep_dive_load(proxy._deep_dive_key(QUESTION)[0])["answer"] == "research #1"
        again = await ask(QUESTION, "chat-b")
        assert len(calls) == 1
        assert "Saved deep dive from" in again and "Press ↻ to redo it." in again
        assert again.endswith("research #1")
    run(case)


def test_same_chat_again_redoes_and_replaces():
    async def case(ask, calls):
        await ask(QUESTION, "chat-a")
        await ask(QUESTION, "chat-b")          # replay
        assert await ask(QUESTION, "chat-b") == "research #2"   # ↻ in chat-b
        assert len(calls) == 2
        assert (await ask(QUESTION, "chat-c")).endswith("research #2")  # new copy saved
        assert len(calls) == 2
    run(case)


def test_fresh_prefix_redoes():
    async def case(ask, calls):
        await ask(QUESTION, "chat-a")
        assert await ask("Fresh " + QUESTION, "chat-b") == "research #2"
        assert (await ask(QUESTION, "chat-c")).endswith("research #2")
    run(case)


def test_no_chat_id_still_replays():
    async def case(ask, calls):
        await ask(QUESTION, "")
        assert "Saved deep dive" in await ask(QUESTION, "")
        assert len(calls) == 1
    run(case)
