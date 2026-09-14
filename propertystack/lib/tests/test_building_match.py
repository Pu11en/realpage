import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.building_match import (
    clean_project_name, is_about_building, is_listing_domain, matches_building,
)


def test_clean_project_name_strips_permit_annotations():
    assert clean_project_name(
        "REVELRY [NEW MIXED-USE] - *LP* / Phased Construction - Type D"
    ) == "REVELRY"
    assert clean_project_name(
        "1020 APACHE [NEW MIXED-USE / MULTI-FAMILY]"
    ) == "1020 APACHE"
    assert clean_project_name("LA VICTORIA COMMONS ON APACHE [EXPEDITED]") == (
        "LA VICTORIA COMMONS ON APACHE"
    )
    assert clean_project_name("VERVE TEMPE [NEW MIXED-USE] (WD)") == "VERVE TEMPE"


def test_clean_project_name_falls_back_to_original_when_emptied():
    assert clean_project_name("[EXPEDITED]") == "[EXPEDITED]"
    assert clean_project_name("") == ""


def test_marquee_on_5th_does_not_match_sports_network():
    assert not matches_building(
        "Marquee on 5th", "500 5th Ave", "https://marqueesportsnetwork.com", "Marquee Sports Network"
    )


def test_marquee_on_5th_does_not_match_st_louis_marquee():
    assert not matches_building(
        "Marquee on 5th", "500 5th Ave", "https://themarqueestl.com", "The Marquee St. Louis"
    )


def test_bella_victoria_matches_its_own_site():
    assert matches_building(
        "Bella Victoria", "1 Bella Victoria Way", "https://bellavictoria.com", "Bella Victoria Apartments"
    )


def test_matches_on_street_address_alone():
    assert matches_building("", "500 5th Ave", "500 5th Ave Tucson AZ new apartments")


def test_no_name_or_address_never_matches():
    assert not matches_building("", "", "https://example.com", "some page")


def test_is_listing_domain_rejects_known_listing_sites():
    assert is_listing_domain("https://www.apartments.com/some-listing")
    assert is_listing_domain("https://www.zillow.com/x")
    assert is_listing_domain("https://rentcafe.com/search")


def test_is_listing_domain_allows_rentcafe_subdomain():
    assert not is_listing_domain("https://legacynorth.rentcafe.com")


def test_is_about_building_rejects_listing_even_with_name_match():
    assert not is_about_building(
        "Bella Victoria", "1 Bella Victoria Way", "https://www.apartments.com/bella-victoria",
        "Bella Victoria Apartments",
    )


def test_is_about_building_accepts_real_site():
    assert is_about_building(
        "Bella Victoria", "1 Bella Victoria Way", "https://bellavictoria.com", "Bella Victoria Apartments"
    )
