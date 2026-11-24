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


def test_calendar_feeds_are_valid_and_never_reveal_findings(tmp_path):
    import json
    from datetime import date
    from radar import config, tracker
    n = tracker.write_calendars(date(2026, 11, 19), tmp_path)
    assert n == len(tracker.coverage())
    flagged = tracker.flagged_meetings()
    headlines = []
    for f in sorted((config.DATA_DIR / "issues").glob("*-findings.json")):
        headlines += [it["headline"] for it in json.loads(f.read_text()) if it.get("headline")]
    for ics in tmp_path.glob("*.ics"):
        raw = ics.read_bytes()
        text = raw.decode("utf-8")
        assert text.startswith("BEGIN:VCALENDAR\r\n") and text.endswith("END:VCALENDAR\r\n")
        assert all(len(line) <= 75 for line in raw.split(b"\r\n"))
        unfolded = text.replace("\r\n ", "")
        assert not any(h in unfolded for h in headlines)
        for block in unfolded.split("BEGIN:VEVENT")[1:]:
            uid = block.split("UID:")[1].split("@")[0].lower()
            assert ("SUMMARY:⚡" in block) == (uid in flagged)
    assert tracker.council_slug("Township of Wellesley") == "township-of-wellesley"


def test_by_hand_calculator_totals_match_council_counts():
    from datetime import date
    from radar import tracker
    today = date(2026, 11, 19)
    data = tracker.council_index(tracker.collect_items(today), today)
    month = data["meta"]["month"]
    assert month["meetings"] == sum(c.get("k", 0) for c in data["councils"])
    assert month["documents"] == sum(c.get("r", 0) for c in data["councils"])
    assert all(c.get("c") for c in data["councils"] if c.get("k"))  # only councils we read


def test_council_pages_are_written_linked_and_never_reveal_findings(tmp_path):
    import json
    from datetime import date
    from radar import config, council_pages, tracker
    today = date(2026, 11, 19)
    index = tracker.council_index(tracker.collect_items(today), today)
    paths = council_pages.write(index, today, tracker.council_slug, tracker._when, tracker._meeting_rank, tmp_path)
    covered = tracker.coverage()
    assert paths[0] == "councils/" and len(paths) - 1 >= len(covered)
    for name in covered:
        assert (tmp_path / tracker.council_slug(name) / "index.html").exists()
    headlines = []
    for f in sorted((config.DATA_DIR / "issues").glob("*-findings.json")):
        headlines += [it["headline"] for it in json.loads(f.read_text()) if it.get("headline")]
    public = {i[2] for c in index["councils"] for i in c.get("i", [])}
    secret = [h for h in headlines if h not in public]
    for page in tmp_path.rglob("index.html"):
        text = page.read_text()
        assert not any(h in text for h in secret)
        assert 'rel="canonical"' in text and "start.js" in text
    hald = (tmp_path / "haldimand-county" / "index.html").read_text()
    assert 'data-councils="Haldimand County"' in hald and "cal/haldimand-county.ics" in hald


def test_share_cards_exist_for_every_page_that_points_to_one(tmp_path):
    import re
    from datetime import date
    from PIL import Image
    from radar import config, council_pages, og_images, tracker
    today = date(2026, 11, 19)
    index = tracker.council_index(tracker.collect_items(today), today)
    pages = tmp_path / "councils"
    council_pages.write(index, today, tracker.council_slug, tracker._when, tracker._meeting_rank, pages)
    og = tmp_path / "og"
    n = og_images.write_all(index, council_pages._upcoming(config.DB_PATH, today, tracker._meeting_rank),
                            tracker.council_slug, tracker._when, og)
    assert n >= 5 + len(tracker.coverage())
    with Image.open(og / "councils" / "haldimand-county.png") as im:
        assert im.size == (1200, 630)
    base = "https://huxleyboivin.github.io/council-radar/og/"
    site_pages = [p for p in (config.ROOT / "site").glob("*.html") if p.name in ("index.html", "brief.html", "sample.html", "tracker.html")]
    for page in list(pages.rglob("index.html")) + site_pages:
        m = re.search(r'og:image" content="([^"]+)"', page.read_text())
        assert m, page
        assert m.group(1).startswith((base, config.SITE_URL + "og/")), m.group(1)
        assert (og / m.group(1).split("/og/", 1)[1]).exists(), m.group(1)


def test_guides_are_written_sourced_and_linked(tmp_path):
    import re
    from datetime import date
    from radar import guides, tracker
    today = date(2026, 11, 20)
    index = tracker.council_index(tracker.collect_items(today), today)
    with_pages = {c["n"]: tracker.council_slug(c["n"]) for c in index["councils"] if c.get("c") or c.get("i")}
    items = tracker.collect_items(today)
    paths = guides.write(today, with_pages, tmp_path, items=items)
    assert paths[0] == "guides/" and len(paths) == 1 + len(guides.PAGES)
    decisions = (tmp_path / "council-decisions" / "index.html").read_text()
    assert decisions.count("<li>") == len([i for i in items if i.get("meeting_date")])  # every public decision listed
    for slug, fn, *_ in guides.PAGES:
        if fn is None:
            continue
        html = (tmp_path / slug / "index.html").read_text()
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        assert len(title.replace("&amp;", "&")) <= 70, title
        assert html.count('rel="nofollow">[source]</a>') >= 3, slug  # every guide cites its facts
        assert '"@type": "FAQPage"' in html and 'rel="canonical"' in html
        for href in re.findall(r'href="\.\./\.\./councils/([^/"]+)/"', html):
            assert href in with_pages.values(), href  # only link council pages that exist
    w1 = (tmp_path / "lt2-window-1-results" / "index.html").read_text()
    assert "Simcoe Battery Project" in w1 and "Dunns Valley Solar" in w1


def test_local_guides_link_both_ways():
    from radar import council_pages, guides
    slugs = {s for s, *_ in guides.PAGES}
    for name, (slug, _) in council_pages.LOCAL_GUIDES.items():
        assert slug in slugs, slug  # every council page points at a guide that exists
        assert f'guides/{slug}/' in council_pages.how_support_works(name, "../../", True, 0)
    assert council_pages.how_support_works("City of Ottawa", "../../", True, 0).count("Local project") == 0


def test_council_page_titles_fit_and_match_meeting_searches():
    from radar import council_pages
    for name in ("Haldimand County", "Municipality of Southwest Middlesex", "Township of Adelaide Metcalfe", "City of Ottawa"):
        t = council_pages.page_title(name)
        assert len(t) <= council_pages.TITLE_MAX and "council" in t.lower() and "meetings" in t, t
    sn = council_pages.search_name
    assert sn("City of Ottawa") == "Ottawa City Council"
    assert sn("County of Oxford") == "Oxford County Council"
    assert sn("Haldimand County") == "Haldimand County Council"
    assert sn("Region of Peel") == "Peel Region Council"
    assert sn("Region of Waterloo") == "Region of Waterloo Council"
    assert sn("Town of Whitby") == "Whitby Council"


def test_custom_domain_switch(tmp_path, monkeypatch):
    from radar import config
    site = tmp_path / "site"
    site.mkdir()
    monkeypatch.setattr(config, "ROOT", tmp_path)
    assert config._site_url() in (config.GITHUB_PAGES_URL, __import__("os").environ.get("RADAR_SITE_URL", config.GITHUB_PAGES_URL))
    (site / "CNAME").write_text("councilradar.ca\n")
    assert config._site_url() == "https://councilradar.ca/"


def test_analytics_tag_on_every_kind_of_page(tmp_path):
    from radar import config, council_pages
    snippet = config.analytics_snippet()
    assert config.ANALYTICS_TAG in snippet and "generate_lead" in snippet
    page = council_pages._shell("t", "d", "https://example.com/", "../", "<main></main>")
    assert snippet in page
    for f in ("index.html", "sample.html", "brief.html"):
        assert (config.ROOT / "site" / f).read_text().count(config.ANALYTICS_TAG) == 1, f



# --- housing beta feed (collect-only) ---

def test_housing_feed_is_live():
    feeds = prefilter.load_feeds()
    h = feeds["housing"]
    assert h.enabled          # launched 2026-11-24 (Huxley)
    assert {"energy", "housing"} <= {k for k, f in feeds.items() if f.enabled}


def test_housing_feed_matches_planning_items_only():
    feeds = prefilter.load_feeds()
    feed = feeds["housing"]
    assert "zba" in feed.categories and "opa" in feed.categories
    for text in ("Recommendation Report: Official Plan Amendment and Zoning By-law Amendment, 120 Main St",
                 "Draft Plan of Subdivision 26T-24001 (Mattamy Homes), 312 units",
                 "Site Plan Approval for a 14-storey mixed-use building",
                 "Request for Council endorsement of a Minister's Zoning Order for 45 Elm Road",
                 "Development Charges By-law update and background study",
                 "Implementation of Bill 185, Cutting Red Tape, Building More Homes Act",
                 "Building Faster Fund allocation and 2031 housing target progress",
                 "appeal to the Ontario Land Tribunal regarding the decision",
                 "Minor Variance A-12/26 to permit an apartment building of 86 units"):
        assert prefilter.excerpt(text, feed)[0] >= 1, text
    for text in ("Minor variance to permit a rear deck 1.2 m from the lot line",
                 "Road resurfacing tender for Main Street.",
                 "CIP: Council Information Package, November 2026",
                 "battery energy storage system support resolution"):
        assert prefilter.excerpt(text, feed) == (0, ""), text
    # the energy feed is untouched by the new block
    assert prefilter.excerpt("Draft Plan of Subdivision 26T-24001", feeds["energy"]) == (0, "")


def test_housing_page_is_live_and_tagged():
    from radar import config
    page = (config.ROOT / "site" / "housing.html").read_text()
    assert page.count(config.ANALYTICS_TAG) == 1
    assert page.count("client_reference_id=housing") >= 2      # founding + team links are tagged
    assert "not yet on sale" not in page
    assert 'href="housing.html"' in (config.ROOT / "site" / "index.html").read_text()


def test_housing_page_uses_housing_stripe_product():
    from radar import config
    page = (config.ROOT / "site" / "housing.html").read_text()
    assert "buy.stripe.com/eVqeVfcwceIv5Ds4Px8Vi02" in page and "buy.stripe.com/4gM00l67O6bZ5DschZ8Vi03" in page
    assert "eVqaEZ3ZGbwjc1Qdm38Vi00?client_reference_id" not in page   # not the energy links
