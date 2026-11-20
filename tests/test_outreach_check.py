import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("outreach_check", Path(__file__).resolve().parent.parent / "tools" / "outreach_check.py")
oc = importlib.util.module_from_spec(spec)
sys.modules["outreach_check"] = oc
spec.loader.exec_module(oc)

SRC = "https://acme-energy.com/contact"


def levels(problems):
    return [p.level for p in problems]


def test_clean_business_address_passes():
    assert oc.check_address("bd@acme-energy.com", "Acme Energy", SRC, [], []) == []


def test_role_inboxes_are_blocked():
    for local in ("media", "Media", "press", "communication", "ir", "communityengagement", "media.relations"):
        probs = oc.check_address(f"{local}@acme-energy.com", "Acme Energy", SRC, [], [])
        assert "BLOCK" in levels(probs), local


def test_personal_and_government_domains_blocked():
    assert "BLOCK" in levels(oc.check_address("jane@gmail.com", "Acme", "https://gmail.com", [], []))
    assert "BLOCK" in levels(oc.check_address("clerk@townofminto.ca", "Minto", "https://townofminto.ca", [], []))
    assert "BLOCK" in levels(oc.check_address("x@ontario.ca", "Ontario", "https://ontario.ca", [], []))


def test_filing_source_and_missing_source_blocked():
    sec = oc.check_address("ceo@acme-energy.com", "Acme", "https://www.sec.gov/Archives/x.htm", [], [])
    assert any("filing" in p.message for p in sec if p.level == "BLOCK")
    assert "BLOCK" in levels(oc.check_address("ceo@acme-energy.com", "Acme", "", [], []))


def test_suppression_by_email_and_domain():
    sup = [{"email_or_domain": "acme-energy.com", "reason": "asked"}]
    assert "BLOCK" in levels(oc.check_address("bd@acme-energy.com", "Acme", SRC, [], sup))
    sup = [{"email_or_domain": "BD@acme-energy.com", "reason": "no thanks"}]
    assert "BLOCK" in levels(oc.check_address("bd@acme-energy.com", "Acme", SRC, [], sup))
    assert oc.check_address("other@acme-energy.com", "Acme", SRC, [], sup) == []


def test_log_rules_one_initial_one_followup():
    log = [{"date": "2026-11-16", "email": "bd@acme-energy.com", "organization": "Acme Energy Inc.",
            "stage": "initial", "status": "sent"}]
    assert "BLOCK" in levels(oc.check_address("bd@acme-energy.com", "Acme Energy", SRC, log, []))
    assert oc.check_address("bd@acme-energy.com", "Acme Energy", SRC, log, [], stage="followup") == []
    log.append({"date": "2026-11-23", "email": "bd@acme-energy.com", "organization": "Acme Energy",
                "stage": "followup", "status": "sent"})
    assert "BLOCK" in levels(oc.check_address("bd@acme-energy.com", "Acme Energy", SRC, log, [], stage="followup"))
    # A colleague at the same organization is a warning, not a block.
    assert set(levels(oc.check_address("jo@acme-energy.com", "Acme Energy (Canada)", SRC, log, []))) == {"WARN"}


def test_opted_out_blocks_followup():
    log = [{"date": "2026-11-16", "email": "bd@acme-energy.com", "organization": "Acme",
            "stage": "initial", "status": "opted_out"}]
    assert "BLOCK" in levels(oc.check_address("bd@acme-energy.com", "Acme", SRC, log, [], stage="followup"))


def test_org_key_matches_variants():
    assert oc.org_key("Blake, Cassels & Graydon LLP (energy group)") == oc.org_key("Blake Cassels & Graydon")
    assert oc.org_key("Neoen (Canada)") == oc.org_key("Neoen")


def test_coverage_uses_repo_data():
    cov = oc.load_coverage()
    status = lambda q: {h["status"] for h in oc.find_council(q, cov)}
    assert status("Haldimand County") == {"read"}
    assert status("Greater Napanee") == {"civicweb"}
    assert status("Prince Edward County") == {"civicweb"}
    assert status("Town of Minto") == {"unknown"}
    assert {h["name"] for h in oc.find_council("Hamilton", cov)} == {"City of Hamilton", "Township of Hamilton"}
    assert oc.coverage_advice("Haldimand", cov) == []
    assert any("not read" in p.message for p in oc.coverage_advice("Napanee", cov))


def test_audit_flags_known_bad_rows_only():
    log = [
        {"date": "2026-11-17", "email": "media@x-energy.com", "organization": "X", "stage": "initial",
         "address_source_url": "https://x-energy.com/news"},
        {"date": "2026-11-17", "email": "bd@y-energy.com", "organization": "Y", "stage": "initial",
         "address_source_url": "https://y-energy.com/contact"},
    ]
    sup = [{"email_or_domain": "media@x-energy.com", "reason": "media inbox"}]
    res = oc.audit(log, sup)
    assert [r["email"] for r, _ in res] == ["media@x-energy.com"]


def test_cli_exit_codes(capsys):
    assert oc.main(["--email", "media@acme-energy.com", "--org", "Acme", "--source", SRC]) == 1
    assert "DO NOT SEND" in capsys.readouterr().out
