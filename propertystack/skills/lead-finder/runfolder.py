"""Run folder, resume, caps, and state pick for the lead-finder chain.

Area-agnostic: the state to run is always chosen from data files, never a
literal in code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

MAX_PROJECTS = 400
MAX_SEARCHES = 900
MIN_PROJECTS_TO_KEEP = 30

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "propertystack" / "data"
RUNS_DIR = REPO_ROOT / "propertystack" / "runs"


def pick_state(targets_path: Path | None = None) -> dict:
    """Pick the state to run next: among the states in targets.json, the one
    with the most permits. Returns {"state": ..., "backup_order": [...]} with the ordered
    backup list (remaining states, same rule, in order).
    """
    targets_path = targets_path or DATA_DIR / "lead-finder-targets" / "targets.json"

    targets = json.loads(targets_path.read_text())

    states = targets["states"]

    ordered = sorted(states, key=lambda entry: -entry.get("permits_5plus_12mo", 0))
    order = [entry["state"] for entry in ordered]
    return {"state": order[0], "backup_order": order}


@dataclass
class RunCaps:
    project_count: int = 0
    jina_searches: int = 0
    brave_searches: int = 0

    @property
    def total_searches(self) -> int:
        return self.jina_searches + self.brave_searches

    def project_cap_hit(self) -> bool:
        return self.project_count >= MAX_PROJECTS

    def search_cap_hit(self) -> bool:
        return self.total_searches >= MAX_SEARCHES

    def any_cap_hit(self) -> bool:
        return self.project_cap_hit() or self.search_cap_hit()

    def below_minimum(self) -> bool:
        """True if the run finished under the roll-into-next-state floor."""
        return self.project_count < MIN_PROJECTS_TO_KEEP


@dataclass
class RunFolder:
    """One run folder per state: propertystack/runs/<state>/<run-id>/.

    One file per step per city; rerunning a step for a city that already has
    its output file skips it (resume).
    """

    state: str
    run_id: str
    runs_dir: Path = field(default=RUNS_DIR)

    @property
    def path(self) -> Path:
        return self.runs_dir / self.state / self.run_id

    def ensure(self) -> Path:
        self.path.mkdir(parents=True, exist_ok=True)
        return self.path

    def step_file(self, step: str, city: str) -> Path:
        safe_city = city.replace(" ", "_").replace("/", "_")
        return self.path / f"{step}.{safe_city}.json"

    def step_done(self, step: str, city: str) -> bool:
        return self.step_file(step, city).exists()

    def save_step(self, step: str, city: str, data) -> Path:
        self.ensure()
        out = self.step_file(step, city)
        out.write_text(json.dumps(data, indent=1))
        return out

    def load_step(self, step: str, city: str):
        return json.loads(self.step_file(step, city).read_text())

    def save_state_pick(self, pick: dict) -> Path:
        self.ensure()
        out = self.path / "state-pick.json"
        out.write_text(json.dumps(pick, indent=1))
        return out

    def load_caps(self) -> RunCaps:
        caps_file = self.path / "caps.json"
        if not caps_file.exists():
            return RunCaps()
        data = json.loads(caps_file.read_text())
        return RunCaps(**data)

    def save_caps(self, caps: RunCaps) -> Path:
        self.ensure()
        out = self.path / "caps.json"
        out.write_text(json.dumps(caps.__dict__, indent=1))
        return out
