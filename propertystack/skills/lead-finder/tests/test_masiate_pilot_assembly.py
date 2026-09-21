"""Synthetic regressions; no network or private worker checkpoints required."""
import copy
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def assembly(monkeypatch):
    tools = Path(__file__).resolve().parents[4] / "tooling" / "masiate_pdf"
    monkeypatch.syspath_prepend(str(tools))
    return importlib.import_module("assemble_pilot")


def fixture_input(assembly, monkeypatch, record_id="synthetic"):
    original = {
        "id": record_id, "county": "Brazos", "project_name": "Test renovation",
        "scope": "Interior renovation", "record_type": "permit", "record_date": "2026-09-01",
        "sources": [{"url": "https://example.test/permit", "title": "Permit"}],
    }
    reviewed = dict(copy.deepcopy(original), review_decision="include")
    contacts = [{"record_ids": [record_id], "verified_business_name": "Test Builder",
                 "role": "contractor", "phone": "555-0100", "email": "test@example.test",
                 "source_url": "https://example.test/contact"}]
    documents = {"review-input/brazos/records.json": [original],
                 "finish/review-brazos/reviewed_records.json": [reviewed],
                 "finish/contacts/contacts.json": contacts}
    monkeypatch.setattr(assembly, "read", lambda p: documents.get(str(p.relative_to(Path('/fixture'))), []))
    return original, reviewed


def test_joins_contacts_without_mutating_inputs(assembly, monkeypatch):
    original, reviewed = fixture_input(assembly, monkeypatch)
    before = copy.deepcopy(reviewed)
    records, watchlist, _, stats, _ = assembly.assemble(Path('/fixture'))
    assert reviewed == before
    assert len(records) == 1 and not watchlist
    assert records[0]['business_contacts'][0]['phone'] == '555-0100'
    assert stats['profiles_with_direct_contact_method'] == 1
    assert stats['source_records_linked_to_detailed_profiles'] == 1
    assert 'Unverified' in records[0]['availability']


def test_upcoming_agenda_moves_to_watchlist(assembly, monkeypatch):
    fixture_input(assembly, monkeypatch, 'grimes-navasota-pz-20260924-pecan-grove-phase2')
    records, watchlist, _, _, audit = assembly.assemble(Path('/fixture'))
    assert not records and len(watchlist) == 1
    assert 'upcoming' in watchlist[0]['priority_reason']
    assert audit[0]['action'] == 'watchlist'


def test_out_of_area_record_cannot_enter_shortlist(assembly, monkeypatch):
    fixture_input(assembly, monkeypatch, next(iter(assembly.GEOGRAPHY_EXCLUSIONS)))
    with pytest.raises(AssertionError, match='Out-of-area'):
        assembly.assemble(Path('/fixture'))


def test_missing_evidence_is_not_silently_accepted(assembly, monkeypatch):
    original, _ = fixture_input(assembly, monkeypatch)
    original['sources'][0]['local_path'] = '/missing/synthetic-evidence.pdf'
    with pytest.raises(AssertionError, match='Missing evidence'):
        assembly.assemble(Path('/fixture'))


def test_public_export_removes_local_evidence_paths(assembly):
    assert assembly.public_data({'sources': [{'local_path': '/tmp/secret.pdf', 'url': 'https://example.test'}],
                                 'evidence_checked': ['/home/user/file', 'https://example.test']}) == {
        'sources': [{'url': 'https://example.test'}], 'evidence_checked': ['https://example.test']}
