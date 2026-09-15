"""Free plan limits through the Open WebUI gateway: questions per day, deep dives per week."""
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

USER = "rep@example.com"
DIVE = "Deep dive on Orchards Market Plaza Senior Apts, Plano (178 units, Entrata)"


def run(case):
    async def go():
        calls = []

        async def hermes(request):
            calls.append(await request.json())
            return web.json_response({"choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": f"answer #{len(calls)}"}}]})

        fake = TestServer(web.Application())
        fake.app.router.add_post("/v1/chat/completions", hermes)
        await fake.start_server()
        app = web.Application()
        app.router.add_post("/v1/chat/completions", proxy.gateway_chat)
        client = TestClient(TestServer(app))
        await client.start_server()
        proxy.HERMES_URL = str(fake.make_url("/v1/chat/completions"))
        proxy.DEEP_DIVE_DIR = tempfile.mkdtemp()
        proxy.GATEWAY_USAGE_FILE = os.path.join(tempfile.mkdtemp(), "usage.json")
        proxy._dive_chats.clear()
        proxy._gateway_hits.clear()

        async def ask(text, email=USER, chat_id="c1", stream=False):
            r = await client.post("/v1/chat/completions", json={
                "model": "hermes-agent", "stream": stream, "messages": [{"role": "user", "content": text}]},
                headers={"Authorization": f"Bearer {proxy.HERMES_KEY}", "X-OpenWebUI-Chat-Id": chat_id,
                         "X-OpenWebUI-User-Email": email})
            if stream:
                return r.status, proxy._sse_text(await r.read())
            return r.status, (await r.json())["choices"][0]["message"]["content"]

        try:
            await case(ask, calls)
        finally:
            await client.close()
            await fake.close()

    asyncio.run(go())


def test_eleventh_question_gets_friendly_limit_message():
    async def case(ask, calls):
        for i in range(10):
            assert (await ask(f"question {i}"))[1].startswith("answer #")
        status, text = await ask("question 11")
        assert status == 200
        assert "used your 10 free questions for today" in text and "cal.com" in text
        assert len(calls) == 10
    run(case)


def test_streaming_limit_message_is_a_normal_answer():
    async def case(ask, calls):
        for i in range(10):
            await ask(f"q{i}")
        status, text = await ask("one more", stream=True)
        assert status == 200 and "free questions" in text
    run(case)


def test_questions_reset_next_day():
    async def case(ask, calls):
        for i in range(10):
            await ask(f"q{i}")
        day, week = proxy._free_keys()
        real = proxy._free_keys
        proxy._free_keys = lambda now=None: ("2099-01-01", week)
        try:
            assert (await ask("new day"))[1].startswith("answer #")
        finally:
            proxy._free_keys = real
    run(case)


def test_admin_and_background_tasks_never_limited():
    async def case(ask, calls):
        for i in range(12):
            assert (await ask(f"q{i}", email=proxy.GATEWAY_ADMIN_EMAIL))[1].startswith("answer #")
        for i in range(10):
            await ask(f"q{i}")
        # Open WebUI title/tags calls are not questions
        assert (await ask("### Task:\nGenerate a concise title"))[1].startswith("answer #")
    run(case)


def test_fourth_deep_dive_in_a_week_blocked_but_questions_still_work():
    async def case(ask, calls):
        for i in range(3):
            assert (await ask(f"Deep dive on Building {i}, Plano (100 units, Yardi)"))[1].startswith("answer #")
        status, text = await ask("Deep dive on Building 9, Plano (100 units, Yardi)")
        assert status == 200 and "3 free deep dives for this week" in text
        assert (await ask("regular question"))[1].startswith("answer #")
    run(case)


def test_replayed_deep_dive_is_free():
    async def case(ask, calls):
        await ask(DIVE, chat_id="a")
        for c in "bcdef":  # replayed from saved, never counted
            assert "Saved deep dive from" in (await ask(DIVE, chat_id=c))[1]
        assert len(calls) == 1
        for i in range(2):  # the first dive used 1 of 3; two fresh ones still allowed
            assert (await ask(f"Deep dive on Building {i}, Plano (100 units, Yardi)"))[1].startswith("answer #")
        assert "3 free deep dives" in (await ask("Deep dive on Building 9, Plano (100 units, Yardi)"))[1]
    run(case)


def test_new_week_resets_deep_dives():
    async def case(ask, calls):
        for i in range(3):
            await ask(f"Deep dive on B{i}, Plano (1 units, Yardi)")
        real = proxy._free_keys
        proxy._free_keys = lambda now=None: (real()[0], "2099-W01")
        try:
            assert (await ask("Deep dive on B7, Plano (1 units, Yardi)"))[1].startswith("answer #")
        finally:
            proxy._free_keys = real
    run(case)


def test_week_starts_monday_central():
    from datetime import datetime
    sun = datetime(2026, 9, 20, 23, 30, tzinfo=proxy.FREE_TZ).timestamp()
    mon = datetime(2026, 9, 21, 0, 30, tzinfo=proxy.FREE_TZ).timestamp()
    assert proxy._free_keys(sun)[0] == "2026-09-20" and proxy._free_keys(mon)[0] == "2026-09-21"
    assert proxy._free_keys(sun)[1] != proxy._free_keys(mon)[1]
