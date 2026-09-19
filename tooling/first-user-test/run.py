"""First-time-user test: an AI (browser-use + DeepSeek) plays a new visitor on the live site and reports confusion.

    ~/.venvs/bu/bin/python tooling/first-user-test/run.py [persona_index ...]

Writes tooling/first-user-test/out/<n>.md. Each run costs a few cents of DeepSeek.
"""
import asyncio, os, sys, pathlib, json
from browser_use import Agent, ChatDeepSeek, BrowserProfile

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
for envf in (HERE.parents[1] / ".env", HERE.parents[1] / "chatbot" / ".env.local"):
    if envf.exists() and not os.environ.get("DEEPSEEK_API_KEY"):
        for line in envf.read_text().splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                os.environ["DEEPSEEK_API_KEY"] = line.split("=", 1)[1].strip()

START = "https://cranesignal.com"
RULES = """
You are a FIRST-TIME visitor. You have never heard of CraneSignal. Behave like a busy real person:
read what the page says, click what looks right, don't inspect code, don't guess URLs.
You do NOT have an account. If the site asks you to sign up or sign in, do NOT sign up — note it and
say whether you understood why and whether you would have signed up.
Spend at most ~20 actions. Then finish with a report in exactly this format:

GOAL REACHED: yes / partly / no
STEPS: numbered list of what you did and what you saw
CONFUSING: every moment you hesitated, were unsure what to click, or didn't understand a word (quote the words)
MISSING: what you expected to find but didn't
FIRST 5 SECONDS: what you thought the site was for after landing
WOULD SIGN UP: yes/no and why
SCORE: 1-10 for how easy it was
"""
PERSONAS = [
    "You are Maria, a sales rep at a company selling property-management software. Your goal: find one apartment building in the Dallas area that is about to pick software, and find out who you should call there.",
    "You are Kevin, a sales manager at a smart-lock / resident-tech company, skeptical of new tools. Your goal: figure out in under 2 minutes what this site gives you, whether the data is real (sources?), and whether it's free.",
    "You are Priya, a marketing lead at a package-locker company, on your PHONE, very busy. Your goal: get a list of leads for Houston you can share with your team.",
    "You are Tom, a business development rep at a leasing-services firm in Phoenix. Your goal: find apartment buildings in Arizona that recently sold (new owners) and see who bought them.",
    "You are Dana, a VP of sales at an apartment internet provider; your market is Tulsa, Oklahoma. Your goal: find leads for Tulsa, and if the site doesn't cover it, find out what you can do about that.",
]

async def run(i):
    mobile = i == 2
    profile = BrowserProfile(headless=True, viewport={"width": 390, "height": 844} if mobile else {"width": 1366, "height": 900},
                             user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" if mobile else None))
    agent = Agent(task=f"Start at {START}.\n{PERSONAS[i]}\n{RULES}", llm=ChatDeepSeek(model="deepseek-chat", api_key=os.environ["DEEPSEEK_API_KEY"]),
                  browser_profile=profile, use_vision=False)
    hist = await agent.run(max_steps=25)
    final = hist.final_result() or "(no final report)"
    urls = [u for u in hist.urls() if u]
    (OUT / f"{i+1}.md").write_text(f"# Persona {i+1}\n\n{PERSONAS[i]}\n\n## Pages visited\n" + "\n".join(dict.fromkeys(urls)) + f"\n\n## Report\n{final}\n")
    print(f"persona {i+1} done")

async def main():
    idx = [int(a) - 1 for a in sys.argv[1:]] or range(len(PERSONAS))
    await asyncio.gather(*(run(i) for i in idx))

asyncio.run(main())
