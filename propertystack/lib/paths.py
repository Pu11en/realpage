"""Shared paths. Every skill reads/writes only inside data/<area>/ and runs/."""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]      # propertystack/
DATA = ROOT / "data"
RUNS = ROOT / "runs"

def area_dir(area: str) -> pathlib.Path:
    d = DATA / area
    d.mkdir(parents=True, exist_ok=True)
    return d
