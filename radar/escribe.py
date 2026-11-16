"""Fetch meetings and documents from eScribe public portals (pub-<slug>.escribemeetings.com).

eScribe exposes a JSON calendar endpoint used by its own portal page. We call it first and
fall back to parsing the portal HTML, so a change in either path doesn't stop collection.
Everything fetched is public meeting material published by the municipality.
"""
from __future__ import annotations

import io
import re
import time
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Iterable
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from . import config

DOC_ID_RE = re.compile(r"filestream\.ashx\?documentid=(\d+)", re.I)
MEETING_ID_RE = re.compile(r"meeting\.aspx\?id=([0-9a-f\-]{36})", re.I)
DATE_FORMATS = ("%Y/%m/%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y-%m-%d",
                "%B %d, %Y", "%b %d, %Y", "%A, %B %d, %Y")


@dataclass
class DocLink:
    doc_id: str
    url: str
    title: str = ""


@dataclass
class Meeting:
    meeting_id: str
    name: str
    start: datetime | None
    url: str
    docs: list[DocLink] = field(default_factory=list)
    has_agenda: bool = True


def base_url(slug: str) -> str:
    return f"https://pub-{slug}.escribemeetings.com"


class Fetcher:
    """Polite HTTP client: identifies itself, honours robots.txt, spaces requests out."""

    def __init__(self, session: requests.Session | None = None, delay: float | None = None):
        self.s = session or requests.Session()
        self.s.headers["User-Agent"] = config.USER_AGENT
        self.delay = config.REQUEST_DELAY_SECONDS if delay is None else delay
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._last = 0.0

    def allowed(self, url: str) -> bool:
        host = urlparse(url).scheme + "://" + urlparse(url).netloc
        rp = self._robots.get(host)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(host + "/robots.txt", timeout=20)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except requests.RequestException:
                rp.parse([])
            self._robots[host] = rp
        return rp.can_fetch(config.USER_AGENT, url)

    def _wait(self):
        gap = time.monotonic() - self._last
        if gap < self.delay:
            time.sleep(self.delay - gap)
        self._last = time.monotonic()

    def get(self, url: str, **kw) -> requests.Response:
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        self._wait()
        r = self.s.get(url, timeout=60, **kw)
        r.raise_for_status()
        return r

    def post_json(self, url: str, payload: dict) -> requests.Response:
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        self._wait()
        r = self.s.post(url, json=payload, timeout=60,
                        headers={"Content-Type": "application/json; charset=utf-8"})
        r.raise_for_status()
        return r


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    m = re.match(r"/Date\((\d+)", value)  # ASP.NET JSON date
    if m:
        return datetime.fromtimestamp(int(m.group(1)) / 1000, timezone.utc).replace(tzinfo=None)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def parse_calendar_json(payload, slug: str) -> list[Meeting]:
    """Parse the GetCalendarMeetings response. Tolerates key-name variations."""
    items = payload.get("d", payload) if isinstance(payload, dict) else payload
    if isinstance(items, dict):
        items = items.get("Meetings") or items.get("meetings") or []
    base = base_url(slug)
    meetings = []
    for it in items or []:
        mid = str(_first(it, "ID", "Id", "id", "MeetingId", default="")).lower()
        url = _first(it, "Url", "URL", "url", default="")
        if not mid and url:
            m = MEETING_ID_RE.search(url)
            mid = m.group(1).lower() if m else ""
        if not mid:
            continue
        # Always use eScribe's canonical agenda address: the calendar's own "Url" field varies
        # by portal (some return paths relative to the calendar service, which 404).
        url = f"Meeting.aspx?Id={mid}&Agenda=Agenda&lang=English"
        docs = []
        for d in _first(it, "MeetingDocumentLink", "Documents", "documents", default=[]) or []:
            durl = _first(d, "Url", "URL", "url", default="")
            m = DOC_ID_RE.search(durl or "")
            if m:
                docs.append(DocLink(m.group(1), urljoin(base + "/", durl),
                                    " ".join(str(_first(d, k, default="")) for k in ("Type", "Title", "Format")).strip()))
        meetings.append(Meeting(
            meeting_id=mid,
            name=str(_first(it, "MeetingName", "Name", "Title", "name", default="Meeting")),
            start=parse_date(str(_first(it, "StartDate", "Start", "start", "Date", default="") or "")),
            url=urljoin(base + "/", url),
            docs=docs,
            has_agenda=bool(it.get("HasAgenda", True)) or bool(docs),
        ))
    return meetings


def parse_portal_html(html: str, slug: str) -> list[Meeting]:
    """Fallback: scrape meeting links (and any visible document links) from the portal page."""
    soup = BeautifulSoup(html, "html.parser")
    base = base_url(slug)
    found: dict[str, Meeting] = {}
    for a in soup.find_all("a", href=True):
        m = MEETING_ID_RE.search(a["href"])
        if not m:
            continue
        mid = m.group(1).lower()
        if mid in found:
            continue
        container = a.find_parent(class_=re.compile("meeting", re.I)) or a.parent
        text = container.get_text(" ", strip=True) if container else a.get_text(" ", strip=True)
        start = None
        dm = re.search(r"([A-Z][a-z]+day, )?([A-Z][a-z]+ \d{1,2}, \d{4})", text)
        if dm:
            start = parse_date(dm.group(2))
        name = a.get_text(" ", strip=True) or "Meeting"
        found[mid] = Meeting(mid, name, start, urljoin(base + "/", a["href"]))
    return list(found.values())


def parse_meeting_page(html: str, slug: str) -> tuple[str, list[DocLink]]:
    """From an agenda (Meeting.aspx) page, return its readable text and all attached documents."""
    soup = BeautifulSoup(html, "html.parser")
    base = base_url(slug)
    docs: dict[str, DocLink] = {}
    for a in soup.find_all("a", href=True):
        m = DOC_ID_RE.search(a["href"])
        if m and m.group(1) not in docs:
            docs[m.group(1)] = DocLink(m.group(1), urljoin(base + "/", a["href"]),
                                       a.get_text(" ", strip=True) or a.get("title", ""))
    for t in soup(["script", "style", "nav", "header", "footer"]):
        t.decompose()
    text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))
    return text, list(docs.values())


def list_meetings(f: Fetcher, slug: str, start: date, end: date) -> list[Meeting]:
    base = base_url(slug)
    try:
        r = f.post_json(base + "/MeetingsCalendarView.aspx/GetCalendarMeetings",
                        {"calendarStartDate": start.isoformat(), "calendarEndDate": end.isoformat()})
        meetings = parse_calendar_json(r.json(), slug)
        if meetings:
            return meetings
    except (requests.RequestException, ValueError, PermissionError):
        pass
    r = f.get(base + "/")
    meetings = parse_portal_html(r.text, slug)
    return [m for m in meetings if m.start is None or start <= m.start.date() <= end]


def agenda_url(meeting: Meeting) -> str:
    q = parse_qs(urlparse(meeting.url).query)
    if "Agenda" in q:
        return meeting.url
    sep = "&" if "?" in meeting.url else "?"
    return meeting.url + f"{sep}Agenda=Agenda&lang=English"


def pdf_text(data: bytes, max_pages: int | None = None) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    pages = reader.pages[: (max_pages or config.MAX_DOC_PAGES)]
    out = []
    for i, p in enumerate(pages, 1):
        try:
            out.append(f"[page {i}]\n" + (p.extract_text() or ""))
        except Exception:  # damaged page; keep going
            continue
    return "\n".join(out)


def fetch_document_text(f: Fetcher, doc: DocLink) -> str:
    r = f.get(doc.url)
    ctype = r.headers.get("Content-Type", "").lower()
    if "pdf" in ctype or r.content[:5] == b"%PDF-":
        return pdf_text(r.content)
    if "html" in ctype or "text" in ctype:
        return BeautifulSoup(r.text, "html.parser").get_text("\n", strip=True)
    return ""  # spreadsheets, images, etc. are skipped


def iter_meeting_documents(f: Fetcher, slug: str, meeting: Meeting) -> Iterable[tuple[str, str, str, str]]:
    """Yield (doc_key, title, url, text) for the agenda page itself and every attachment."""
    html = f.get(agenda_url(meeting)).text
    agenda_text, page_docs = parse_meeting_page(html, slug)
    yield (f"{slug}:agenda:{meeting.meeting_id}", f"{meeting.name} agenda", agenda_url(meeting), agenda_text)
    seen = set()
    for d in meeting.docs + page_docs:
        if d.doc_id in seen:
            continue
        seen.add(d.doc_id)
        yield (f"{slug}:doc:{d.doc_id}", d.title, d.url, None)  # text fetched lazily by caller
