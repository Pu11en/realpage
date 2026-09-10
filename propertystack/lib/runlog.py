"""Run log: every skill run writes runs/<timestamp>-<skill>.json (feeds the Under the Hood page)."""
import json, time, datetime as dt
from .paths import RUNS

class RunLog:
    def __init__(self, skill: str, area: str):
        self.rec = {"skill": skill, "area": area, "started": dt.datetime.now().isoformat(timespec="seconds"),
                    "inputs": [], "outputs": [], "counts": {}, "api_calls": {}, "errors": [], "notes": []}
        self._t = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.rec["errors"].append(f"{exc_type.__name__}: {exc}")
        self.rec["finished"] = dt.datetime.now().isoformat(timespec="seconds")
        self.rec["duration_s"] = round(time.time() - self._t, 1)
        self.rec["status"] = "error" if exc else "ok"
        RUNS.mkdir(exist_ok=True)
        ts = self.rec["started"].replace(":", "").replace("-", "")
        (RUNS / f"{ts}-{self.rec['skill']}.json").write_text(json.dumps(self.rec, indent=2))
        return False
