import json
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from radar import analyze, digest, escribe, prefilter, store
from radar import __main__ as cli

CAL = {"d": [{
    "ID": "6F1A2B3C-0000-4000-8000-1234567890AB",
    "MeetingName": "Council Meeting",
    "StartDate": "2026/11/24 18:00:00",
    "Url": "Meeting.aspx?Id=6f1a2b3c-0000-4000-8000-1234567890ab&Agenda=Agenda&lang=English",
    "MeetingDocumentLink": [{"Type": "Agenda", "Format": "PDF", "Title": "Agenda",
                             "Url": "FileStream.ashx?DocumentId=4411"}],
}]}

PORTAL = """<html><body><div class="meeting-item"><h3>Council Meeting</h3>
<span>Monday, November 24, 2026</span>
<a href="Meeting.aspx?Id=6f1a2b3c-0000-4000-8000-1234567890ab&Agenda=Agenda&lang=English">Council Meeting</a>
</div></body></html>"""

AGENDA = """<html><body><h1>Council Agenda</h1>
<p>8.1 Request for Municipal Support Confirmation - Battery Energy Storage System, 123 Concession Rd</p>
<a href="FileStream.ashx?DocumentId=4412">Staff Report PW-2026-14 Municipal Support Confirmation BESS</a>
<a href="filestream.ashx?DocumentId=4412">duplicate</a>
<a href="FileStream.ashx?DocumentId=4413">Minutes of previous meeting</a>
<script>var x=1</script></body></html>"""

REPORT_TEXT = ("Staff Report PW-2026-14. Subject: Request for Municipal Support Confirmation. "
               "Acme Storage Inc. requests a Municipal Support Confirmation for a 50 MW battery energy "
               "storage system (BESS) at 123 Concession Rd for the IESO LT2 Window 2 procurement. "
               "Staff recommend that Council defer the request until a protocol is adopted.")


def test_parse_calendar_json():
    ms = escribe.parse_calendar_json(CAL, "examplecounty")
    assert len(ms) == 1
    m = ms[0]
    assert m.meeting_id == "6f1a2b3c-0000-4000-8000-1234567890ab"
    assert m.start == datetime(2026, 11, 24, 18, 0)
    assert m.url.startswith("https://pub-examplecounty.escribemeetings.com/Meeting.aspx")
    assert m.docs[0].doc_id == "4411"


def test_calendar_html_pages_and_bot_gate():
    cal = {"d": [{"ID": "6f1a2b3c-0000-4000-8000-1234567890ab", "MeetingName": "Council",
                  "StartDate": "2026/11/24 18:00:00", "HasAgenda": True, "MeetingDocumentLink": [
                      {"Type": "Agenda", "Url": "/FileStream.ashx?DocumentId=1"},
                      {"Type": "Agenda", "Url": "/Meeting.aspx?Id=6f1a2b3c-0000-4000-8000-1234567890ab&Agenda=Agenda&lang=English"},
                      {"Type": "PostMinutes", "Url": "/Meeting.aspx?Id=6f1a2b3c-0000-4000-8000-1234567890ab&Agenda=PostMinutes&lang=English"}]}]}
    m = escribe.parse_calendar_json(cal, "x")[0]
    assert [k for k, _ in m.html_pages] == ["Agenda", "PostMinutes"]
    blocked = SimpleNamespace(status_code=403, headers={"Server": "cloudflare"}, text="<title>Verifying you are human</title>")
    assert escribe.is_challenge(blocked)
    assert not escribe.is_challenge(SimpleNamespace(status_code=200, headers={}, text="ok"))


def test_parse_portal_html_fallback():
    ms = escribe.parse_portal_html(PORTAL, "examplecounty")
    assert len(ms) == 1 and ms[0].start == datetime(2026, 11, 24)


def test_parse_meeting_page_dedupes_and_strips_scripts():
    text, docs = escribe.parse_meeting_page(AGENDA, "examplecounty")
    assert [d.doc_id for d in docs] == ["4412", "4413"]
    assert "Battery Energy Storage" in text and "var x" not in text


def test_parse_date_variants():
    assert escribe.parse_date("/Date(1795545600000)/").year == 2026
    assert escribe.parse_date("2026-11-24T18:00:00") == datetime(2026, 11, 24, 18)
    assert escribe.parse_date("nonsense") is None


def test_prefilter_matches_energy_only():
    feed = prefilter.load_feeds()["energy"]
    hits, ex = prefilter.excerpt(REPORT_TEXT, feed)
    assert hits >= 3 and "BESS" in ex
    assert prefilter.excerpt("Road resurfacing tender for Main Street.", feed) == (0, "")


class FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
        self.messages = self

    def create(self, **kw):
        self.calls += 1
        return SimpleNamespace(content=[SimpleNamespace(text=self.payload)])


AI_JSON = json.dumps([{
    "category": "support_request", "headline": "Acme Storage seeks support for 50 MW BESS",
    "project": "123 Concession Rd", "proponent": "Acme Storage Inc.", "technology": "BESS",
    "capacity_mw": 50, "status": "recommended",
    "summary": "Staff recommend deferring Acme's request until a protocol is adopted.",
    "evidence": "Staff recommend that Council defer the request until a protocol is adopted.",
    "confidence": 0.9}, {"category": "made_up", "headline": "", "summary": ""}])


def test_analyze_read_cleans_output():
    feed = prefilter.load_feeds()["energy"]
    out = analyze.read(feed, REPORT_TEXT, {"doc_title": "t", "municipality": "m", "meeting_name": "n",
                                           "meeting_date": "2026-11-24", "url": "u"},
                       client=FakeClient("Here you go:\n" + AI_JSON))
    assert len(out) == 1 and out[0]["capacity_mw"] == 50.0 and out[0]["category"] == "support_request"


def test_digest_render():
    rows = [{"id": 1, "category": "support_request", "municipality": "Example County",
             "headline": "Acme seeks support", "status": "recommended", "meeting_name": "Council",
             "meeting_date": "2026-11-24", "technology": "BESS", "capacity_mw": 50.0,
             "proponent": "Acme", "summary": "S", "evidence": "E", "source_url": "https://x"}]
    subject, body = digest.render(rows, "Council Radar: Test", date(2026, 11, 16))
    assert "November 16, 2026" in subject
    assert "## New support requests" in body and "50 MW" in body and "[Read the source document](https://x)" in body


def test_slug_candidates():
    assert cli.slug_candidates("Haldimand (County)")[:3] == ["haldimand", "haldimand", "haldimandcounty"] or \
        "haldimandcounty" in cli.slug_candidates("Haldimand (County)")
    assert "greatersudbury" in cli.slug_candidates("Greater Sudbury (City)")
    assert "bluemountains" in cli.slug_candidates("The Blue Mountains (Town)")
    assert cli.display_name(*cli.parse_name_line("Minto (Town)")) == "Town of Minto"


def test_no_cost_mode_saves_excerpts_then_renders(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli.config, "DB_PATH", tmp_path / "radar.db")
    monkeypatch.setattr(store.config, "DB_PATH", tmp_path / "radar.db")
    monkeypatch.setattr(cli.config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cli.config, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(cli, "load_municipalities",
                        lambda: [{"name": "Example County", "platform": "escribe", "slug": "examplecounty"}])
    meeting = escribe.parse_calendar_json(CAL, "examplecounty")[0]
    monkeypatch.setattr(escribe, "list_meetings", lambda f, s, a, b: [meeting])
    monkeypatch.setattr(escribe, "iter_meeting_documents",
                        lambda f, slug, m: iter([("examplecounty:doc:4412", "Staff report", "https://r", REPORT_TEXT),
                                                 ("examplecounty:doc:9", "Roads", "https://x", "Road resurfacing.")]))
    assert cli.main(["run"]) == 0
    capsys.readouterr()
    assert cli.main(["pending", "--since", "0000-00-00"]) == 0
    pending = json.loads(capsys.readouterr().out)
    assert pending["count"] == 1 and pending["excerpts"][0]["municipality"] == "Example County"
    assert "BESS" in pending["excerpts"][0]["excerpt"]
    assert cli.main(["run"]) == 0  # unchanged document is not saved twice
    capsys.readouterr()
    cli.main(["pending", "--since", "0000-00-00"])
    assert json.loads(capsys.readouterr().out)["count"] == 1

    findings = tmp_path / "f.json"
    findings.write_text(json.dumps([{"category": "support_request", "municipality": "Example County",
                                     "headline": "Acme seeks support", "status": "recommended",
                                     "summary": "S", "source_url": "https://r"}]))
    assert cli.main(["render", "--findings", str(findings), "--mark-done"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert Path(out["path"]).read_text().count("Acme seeks support") == 1
    assert (tmp_path / "issues" / "last_issue.txt").exists()


def test_run_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.config, "DB_PATH", tmp_path / "radar.db")
    monkeypatch.setattr(store.config, "DB_PATH", tmp_path / "radar.db")
    monkeypatch.setattr(cli.config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cli.config, "ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(cli, "load_municipalities",
                        lambda: [{"name": "Example County", "platform": "escribe", "slug": "examplecounty"}])
    meeting = escribe.parse_calendar_json(CAL, "examplecounty")[0]
    monkeypatch.setattr(escribe, "list_meetings", lambda f, s, a, b: [meeting])

    def fake_docs(f, slug, m):
        yield ("examplecounty:agenda:x", "Council agenda", "https://a", "Agenda item: municipal support confirmation BESS")
        yield ("examplecounty:doc:4412", "Staff report", "https://r", None)
    monkeypatch.setattr(escribe, "iter_meeting_documents", fake_docs)
    monkeypatch.setattr(escribe, "fetch_document_text", lambda f, d: REPORT_TEXT)
    fake = FakeClient(AI_JSON)
    monkeypatch.setattr(analyze, "_client", lambda: fake)

    assert cli.main(["run"]) == 0
    con = store.connect(tmp_path / "radar.db")
    rows = con.execute("SELECT * FROM findings").fetchall()
    assert len(rows) == 1  # same finding from agenda + report is deduplicated
    assert rows[0]["municipality"] == "Example County"
    calls_after_first = fake.calls
    assert cli.main(["run"]) == 0  # second run: report unchanged, nothing re-read
    assert fake.calls == calls_after_first  # agenda re-fetched but unchanged, so no new AI read


def test_tracker_delays_live_findings_and_hides_signals(tmp_path, monkeypatch):
    import json
    from datetime import date
    from radar import config, tracker
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    (tmp_path / "issues").mkdir()
    live = [
        {"category": "support_granted", "municipality": "Town A", "headline": "Old grant", "meeting_date": "2026-10-01"},
        {"category": "support_granted", "municipality": "Town B", "headline": "Fresh grant", "meeting_date": "2026-11-12"},
        {"category": "delegation", "municipality": "Town C", "headline": "Early signal", "meeting_date": "2026-09-01"},
    ]
    (tmp_path / "issues" / "2026-11-16-energy-findings.json").write_text(json.dumps(live))
    heads = {i["headline"] for i in tracker.collect_items(date(2026, 11, 16))}
    assert "Old grant" in heads
    assert "Fresh grant" not in heads      # subscribers get it first
    assert "Early signal" not in heads     # signals stay subscriber-only


def test_prefilter_catches_common_bess_and_solar_phrasings():
    feed = prefilter.load_feeds()["energy"]
    for text in ("consent for a lease of 22 years to facilitate a battery storage facility",
                 "a proposed battery facility on agricultural lands",
                 "ground-mounted solar array on the property",
                 "construction of wind turbines"):
        assert prefilter.excerpt(text, feed)[0] >= 1, text
    for text in ("Museum Storage Lease Agreement", "bicycle storage and waste enclosure",
                 "replace the smoke detector battery"):
        assert prefilter.excerpt(text, feed) == (0, ""), text


def test_council_lookup_counts_subscriber_items_without_revealing_them(tmp_path, monkeypatch):
    import json
    from datetime import date
    from radar import config, tracker
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "none.db")
    (tmp_path / "issues").mkdir()
    (tmp_path / "ontario_municipalities.txt").write_text("# header\nHaldimand (County)\nMinto (Town)\n")
    live = [
        {"category": "support_granted", "municipality": "Haldimand County", "headline": "Public grant", "meeting_date": "2026-10-01"},
        {"category": "zoning_bylaw", "municipality": "Haldimand County", "headline": "Secret lease hearing", "meeting_date": "2026-11-12"},
    ]
    (tmp_path / "issues" / "2026-11-16-energy-findings.json").write_text(json.dumps(live))
    today = date(2026, 11, 16)
    data = tracker.council_index(tracker.collect_items(today), today)
    blob = json.dumps(data)
    assert "Secret lease hearing" not in blob          # subscriber items are counted, never shown
    hald = next(c for c in data["councils"] if c["n"] == "Haldimand County")
    assert hald["l"] == 1
    assert any(i[2] == "Public grant" for i in hald["i"])
    assert any(c["n"] == "Town of Minto" and not c.get("c") for c in data["councils"])


def test_council_lookup_includes_published_sample_signals():
    from datetime import date
    from radar import tracker
    today = date(2026, 11, 18)
    data = tracker.council_index(tracker.collect_items(today), today)
    wellesley = next(c for c in data["councils"] if c["n"] == "Township of Wellesley")
    assert any(i[0] == "delegation" for i in wellesley.get("i", []))
    assert not wellesley.get("l")  # a published signal is never counted as subscriber-only
