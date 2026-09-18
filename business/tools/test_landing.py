#!/usr/bin/env python3
"""Test the landing page for investors."""

import re
import sys
from pathlib import Path

def load_landing_page():
    """Load the landing page HTML."""
    landing_path = Path(__file__).parent.parent / "marketing" / "landing" / "index.html"
    if not landing_path.exists():
        raise FileNotFoundError(f"Landing page not found: {landing_path}")
    return landing_path.read_text()

def test_landing_page():
    """Run all landing page tests."""
    html = load_landing_page()
    failures = []

    # Test 1: Contains the investor headline (check for key phrases)
    if not ("apartment buildings" in html and "just sold" in html and "who bought them" in html and "what's being built" in html):
        failures.append("❌ Missing investor headline or key phrases")

    # Test 2: Contains "Start free" button/link
    if not re.search(r'start\s+free', html, re.IGNORECASE):
        failures.append("❌ Missing 'Start free' button")

    # Test 3: No RealPage text
    if re.search(r'realpage', html, re.IGNORECASE):
        failures.append("❌ Contains 'RealPage' text (should be removed for investor focus)")

    # Test 4: Contains example lead card
    if "Legacy Arapaho" not in html or "250 E Arapaho Rd" not in html:
        failures.append("❌ Missing example lead card (Legacy Arapaho building)")

    # Test 5: Contains "CraneSignal" branding
    if "CraneSignal" not in html:
        failures.append("❌ Missing CraneSignal branding")

    # Test 6: Contains "Why early" and "The list" navigation
    if "Why early" not in html or "The list" not in html:
        failures.append("❌ Missing navigation items")

    # Test 7: No login requirement visible
    if "sign in" in html.lower() and "already have one" in html.lower():
        # This is okay - it's part of the "Already have one? Sign in" link in the chat panel
        # Just make sure the main page doesn't require sign-in
        if "form" in html.lower() and "password" in html.lower():
            failures.append("❌ Page contains login form (should not)")

    # Test 8: Contains "Most sites find out too late"
    if "Most sites find out too late" not in html:
        failures.append("❌ Missing footer tagline")

    # Report results
    if failures:
        print("\n".join(failures))
        return False
    else:
        print("✅ All landing page tests passed")
        return True

if __name__ == "__main__":
    success = test_landing_page()
    sys.exit(0 if success else 1)
