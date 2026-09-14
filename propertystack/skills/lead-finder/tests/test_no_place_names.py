"""Fails if any lead-finder-* skill's code has a literal US place name.

The lead finder must work for any state picked at run time (PLAN-lead-finder-build.md,
Part 1.1). Comments, docstrings and code alike are checked, since a hard-coded name in a
comment is still a sign the logic secretly assumes one place.
"""
import pathlib
import re

SKILLS_ROOT = pathlib.Path(__file__).resolve().parents[2]  # propertystack/skills/

# Code files only -- data files (csv/json) are allowed to name real places.
CODE_SUFFIXES = {".py"}

US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
    "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
    "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
]

BIG_CITIES_AND_COUNTIES = [
    "Plano", "Richardson", "Collin", "Dallas", "Fort Worth", "Houston", "Austin",
    "San Antonio", "Phoenix", "Atlanta", "Charlotte", "Raleigh", "Nashville",
    "Denver", "Tampa", "Orlando", "Jacksonville", "Las Vegas", "Miami",
]

BANNED = US_STATES + BIG_CITIES_AND_COUNTIES

# Word-boundary, case-sensitive (avoids matching e.g. "washington" as a common noun
# fragment, and lets fixture files use lowercase placeholders freely).
BANNED_RE = re.compile(r"\b(" + "|".join(re.escape(name) for name in BANNED) + r")\b")


THIS_FILE = pathlib.Path(__file__).resolve()


def _lead_finder_code_files():
    for skill_dir in SKILLS_ROOT.glob("lead-finder*"):
        if not skill_dir.is_dir():
            continue
        for path in skill_dir.rglob("*"):
            if (
                path.is_file()
                and path.suffix in CODE_SUFFIXES
                and "fixtures" not in path.parts
                and path.resolve() != THIS_FILE
            ):
                yield path


def test_no_place_names_in_lead_finder_code():
    offenders = []
    for path in _lead_finder_code_files():
        text = path.read_text(errors="ignore")
        for match in BANNED_RE.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            offenders.append(f"{path}:{line_no}: {match.group(0)!r}")
    assert not offenders, "place name(s) found in lead-finder code:\n" + "\n".join(offenders)


def test_lead_finder_skill_dirs_exist():
    assert (SKILLS_ROOT / "lead-finder").is_dir()
