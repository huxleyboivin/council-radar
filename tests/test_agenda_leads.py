import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import agenda_leads as al  # noqa: E402


def _excerpt(tmp, day, name, municipality, date, text, feed="housing"):
    d = tmp / day
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{feed}__{name}.json").write_text(json.dumps({
        "feed": feed, "municipality": municipality, "meeting_date": date, "meeting_name": "Council",
        "url": f"https://pub-x.escribemeetings.com/{name}", "excerpt": text}))


def test_extract_finds_firms_after_application_cues():
    text = ("Application submitted by The Jones Consulting Group Ltd., on behalf of Piveon Developments, to rezone "
            "lands. Agent: Humphries Planning Group Inc. Recommendation: That Report GMS-PL-2026 be received.")
    orgs = [o for o, _ in al.extract(text)]
    assert "Jones Consulting Group Ltd" in orgs
    assert "Piveon Developments" in orgs
    assert any(o.startswith("Humphries Planning Group") for o in orgs)


def test_extract_skips_people_public_bodies_and_numbered_companies():
    text = ("Applicant: Azeem Iqbal Location: 416 Miller Park Avenue. Owner: 1234567 Ontario Inc. "
            "submitted by the City of Barrie Planning. on behalf of the Corporation of the Town of Whitby.")
    assert al.extract(text) == []


def test_collect_ranks_by_councils_and_drops_known_orgs(tmp_path):
    _excerpt(tmp_path, "2026-11-20", "a", "City of Guelph", "2026-11-19", "Agent: Nethery Planning re: 5 Main St")
    _excerpt(tmp_path, "2026-11-21", "b", "Town of Erin", "2026-11-25", "submitted by Nethery Planning, for a ZBA")
    _excerpt(tmp_path, "2026-11-21", "c", "Town of Erin", "2026-11-25", "Agent: Weston Consulting Inc. for 12 units")
    _excerpt(tmp_path, "2026-11-21", "d", "Town of Erin", "2026-11-25", "Agent: Spriet Associates", feed="energy")
    leads = al.collect("housing", root=tmp_path, known={"weston"})
    assert [l.organization for l in leads] == ["Nethery Planning"]
    top = leads[0]
    assert top.councils == {"City of Guelph", "Town of Erin"} and top.latest == "2026-11-25"
    assert top.kind == "consultant" and top.evidence_url.endswith("/b")


def test_known_orgs_reads_names_and_email_domains(tmp_path):
    (tmp_path / "log.csv").write_text("organization,email\nKLM Planning Partners Inc.,goodplanning@klmplanning.com\n")
    known = al.known_orgs([tmp_path / "log.csv"])
    assert al.is_known("KLM Planning", known)
    assert not al.is_known("Nethery Planning", known)


def test_write_marks_every_lead_needs_address(tmp_path):
    lead = al.Lead("Thorstone Planning", {"Township of King"}, {("Township of King", "2026-11-30", "Council")},
                   "2026-11-30", "https://pub-king.escribemeetings.com/x", "Agent: Thorstone Planning")
    out = tmp_path / "leads.csv"
    al.write([lead], out)
    rows = out.read_text().splitlines()
    assert rows[0].startswith("feed,organization,kind") and rows[1].endswith("needs_address")
    assert "@" not in out.read_text()  # never an address
