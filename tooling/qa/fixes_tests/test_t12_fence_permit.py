"""T12: a fence permit ("Multi-Family New Perimeter Fence") is not an apartment lead."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "propertystack" / "skills" / "lead-finder"))

from junk_permits import is_junk_permit  # noqa: E402


def test_perimeter_fence_permit_is_junk():
    assert is_junk_permit("Multi-Family New Perimeter Fence")


def test_fence_permit_variants_are_junk():
    assert is_junk_permit("New Perimeter Fence")
    assert is_junk_permit("Fence Replacement")


def test_real_apartment_project_is_not_junk():
    assert not is_junk_permit("Multi-Family New Construction - 250 units")


def test_street_named_fence_is_not_junk():
    assert not is_junk_permit("New building at 100 Fence Rd")
