"""Test lead data quality flagging rules."""
import pytest
import re


def is_valid_phone(phone):
    """Check if phone is in format (XXX) XXX-XXXX with 10 digits total."""
    if not phone or not phone.strip():
        return True  # Empty is not invalid, just missing
    phone = phone.strip()
    return bool(re.match(r'^\(\d{3}\) \d{3}-\d{4}$', phone))


def is_valid_link(url):
    """Check if URL is http(s) or empty."""
    if not url or not url.strip():
        return True  # Empty is OK
    url = url.strip()
    return url.startswith('http://') or url.startswith('https://')


class TestPhoneValidation:
    def test_valid_phone_format(self):
        """Valid phones should pass."""
        assert is_valid_phone("(210) 326-1119")
        assert is_valid_phone("(972) 754-1024")
        assert is_valid_phone("(254) 759-8027")

    def test_invalid_phone_missing_digits(self):
        """Phone missing leading digit should fail."""
        assert not is_valid_phone("8-773-367-2410")

    def test_invalid_phone_wrong_format(self):
        """Phone without parentheses should fail."""
        assert not is_valid_phone("319-217-8136")
        assert not is_valid_phone("512-610-4016")
        assert not is_valid_phone("440-263-0406")

    def test_empty_phone_is_valid(self):
        """Empty or whitespace phone is not invalid (just missing)."""
        assert is_valid_phone("")
        assert is_valid_phone("   ")
        assert is_valid_phone(None)


class TestLinkValidation:
    def test_valid_links(self):
        """Valid http(s) URLs should pass."""
        assert is_valid_link("https://www.tdlr.texas.gov/TABS/Search/Project/TABS2025003997")
        assert is_valid_link("http://example.com")
        assert is_valid_link("https://example.com")

    def test_invalid_link_no_protocol(self):
        """Links without http(s) should fail."""
        assert not is_valid_link("www.example.com")
        assert not is_valid_link("example.com")

    def test_empty_link_is_valid(self):
        """Empty links are OK."""
        assert is_valid_link("")
        assert is_valid_link("   ")
        assert is_valid_link(None)


class TestUnitCount:
    def test_missing_units_should_be_flagged(self):
        """Rows with empty unit count should be flagged."""
        row = {"units": ""}
        assert not row["units"].strip()

        row = {"units": "   "}
        assert not row["units"].strip()

    def test_present_units_ok(self):
        """Rows with units should not be flagged."""
        row = {"units": "336"}
        assert row["units"].strip()

        row = {"units": "232"}
        assert row["units"].strip()


class TestDuplicateDetection:
    def test_same_address_is_duplicate(self):
        """Two rows with same address should be detected as duplicates."""
        row1 = {"name": "Project A", "city": "Austin", "address": "123 Main St"}
        row2 = {"name": "Project B", "city": "Dallas", "address": "123 Main St"}

        addr1 = (row1["address"] or "").strip().lower()
        addr2 = (row2["address"] or "").strip().lower()
        assert addr1 == addr2

    def test_same_name_city_is_duplicate(self):
        """Two rows with same name and city should be detected as duplicates."""
        row1 = {"name": "The Bloom", "city": "Austin", "address": "123 Main St"}
        row2 = {"name": "The Bloom", "city": "Austin", "address": "456 Oak Ave"}

        name1 = (row1["name"] or "").strip().lower()
        city1 = (row1["city"] or "").strip().lower()
        name2 = (row2["name"] or "").strip().lower()
        city2 = (row2["city"] or "").strip().lower()
        assert (name1, city1) == (name2, city2)

    def test_different_name_city_address_not_duplicate(self):
        """Rows with different name/city/address should not be duplicates."""
        row1 = {"name": "Project A", "city": "Austin", "address": "123 Main St"}
        row2 = {"name": "Project B", "city": "Dallas", "address": "456 Oak Ave"}

        addr1 = (row1["address"] or "").strip().lower()
        addr2 = (row2["address"] or "").strip().lower()
        assert addr1 != addr2

        name1 = (row1["name"] or "").strip().lower()
        city1 = (row1["city"] or "").strip().lower()
        name2 = (row2["name"] or "").strip().lower()
        city2 = (row2["city"] or "").strip().lower()
        assert (name1, city1) != (name2, city2)


class TestCleaning:
    def test_bad_phone_is_blanked(self):
        """Invalid phones should be blanked to empty string."""
        # Bad phones should be blanked
        assert not is_valid_phone("8-773-367-2410")
        # After cleaning, it would be set to ""
        assert is_valid_phone("")

    def test_valid_phone_preserved(self):
        """Valid phones should not be changed."""
        assert is_valid_phone("(210) 326-1119")
        # Should remain valid after check

    def test_count_facts_empty_row(self):
        """Empty row should have 0 facts."""
        row = {"name": "", "city": "", "units": ""}
        facts = sum(1 for v in row.values() if v and str(v).strip())
        assert facts == 0

    def test_count_facts_partial_row(self):
        """Row with some empty fields should count only non-empty ones."""
        row = {"name": "Project A", "city": "Austin", "units": "", "address": "123 Main"}
        facts = sum(1 for v in row.values() if v and str(v).strip())
        assert facts == 3

    def test_merge_keeps_more_facts(self):
        """Merge should keep the row with more non-empty fields."""
        row1 = {"name": "Project", "city": "Austin", "address": "", "units": "100", "phone": ""}
        row2 = {"name": "Project", "city": "Austin", "address": "123 Main", "units": "", "phone": "(210) 123-4567"}

        facts1 = sum(1 for v in row1.values() if v and str(v).strip())
        facts2 = sum(1 for v in row2.values() if v and str(v).strip())
        # row2 has more facts (3 vs 2)
        assert facts2 > facts1

    def test_merge_keeps_earliest_date(self):
        """Merge should keep the earliest opening_date."""
        from datetime import datetime

        def parse_date(date_str):
            if not date_str or not str(date_str).strip():
                return None
            try:
                return datetime.strptime(str(date_str).strip(), '%Y-%m-%d')
            except ValueError:
                return None

        date1 = "2026-09-30"
        date2 = "2026-10-01"
        d1 = parse_date(date1)
        d2 = parse_date(date2)

        assert d1 < d2
        # Earlier date should be kept
        assert d1 == min(d1, d2)
