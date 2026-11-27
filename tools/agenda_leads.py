"""Turn the agenda packages we already read into a ranked list of housing (or energy) leads.

Why (weekly review, 2026-11-27): outreach ran dry. Every org in outreach/prospects.csv has been
emailed or ruled out, and the outreach runs can't fetch web pages from the cloud, so they keep
ending with "no new prospects". Meanwhile data/excerpts/ holds hundreds of agenda passages that
name the planning consultants and builders who file applications at the councils we read. Those
firms are the housing edition's buyers, and each comes with a checkable hook (their own file on a
named council's agenda this month).

This tool finds organisations named next to application cues ("submitted by", "Agent:",
"Applicant:", "on behalf of", "c/o", "prepared by"), keeps only corporate names (never private
individuals or numbered companies), drops public bodies and anyone we've already contacted or
listed, and ranks them by how many councils and meetings they appear at.

It never finds or guesses email addresses. A lead becomes a prospect only after someone (the
chief of staff, outreach run or browser desk) records an address the firm publishes itself,
under the rules in ops/outreach_task.md.

Usage:
  python tools/agenda_leads.py                      # housing, prints the top 25
  python tools/agenda_leads.py --feed energy --top 10
  python tools/agenda_leads.py --write              # also writes outreach/agenda_leads.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCERPTS = ROOT / "data" / "excerpts"
OUT = ROOT / "outreach" / "agenda_leads.csv"
KNOWN_FILES = [ROOT / "outreach" / n for n in ("prospects.csv", "log.csv", "named_contacts.csv", "suppression.csv")]

CUE = re.compile(r"(?i)\b(submitted by|agent|applicant|owner|on behalf of|c/o|prepared by|proponent)\b\s*[:,\-–]?\s*")
SUFFIX = (r"(?:Planning(?: Group| Limited| Ltd\.?| Inc\.?)?|Consulting(?: Group)?(?: Ltd\.?| Inc\.?| Limited)?|"
          r"Consultants(?: Inc\.?| Ltd\.?| Limited)?|Associates(?: Ltd\.?| Inc\.?| Limited)?|"
          r"Developments?(?: Inc\.?| Ltd\.?| Limited| Corp\.?)?|Homes(?: Inc\.?| Ltd\.?| Limited)?|"
          r"Properties(?: Inc\.?| Ltd\.?| Limited)?|Holdings(?: Inc\.?| Ltd\.?| Limited)?|Group(?: Inc\.?| Ltd\.?)?|"
          r"Communities(?: Inc\.?)?|Realty(?: Inc\.?)?|Builders?(?: Inc\.?)?|Engineering(?: Inc\.?| Ltd\.?)?|"
          r"Inc\.|Ltd\.|Limited|LLP|Corp\.|Corporation)")
# A name is 1-6 capitalised words (allowing &, initials, apostrophes, hyphens) ending in a corporate suffix.
NAME = re.compile(r"((?:(?:[A-Z][\w'’.\-]*|&|and|of)\s+){0,5}?(?:[A-Z][\w'’.\-]*\s+)?" + SUFFIX + r")(?=[\s,.;:)]|$)")

PUBLIC = re.compile(r"(?i)\b(city|town|township|county|region|regional|municipal|municipality|ministry|province|"
                    r"provincial|ontario land tribunal|tribunal|council|committee|conservation|hydro|school board|"
                    r"housing corporation|build canada|canada mortgage|tourism|services corporation|enterprises corporation|"
                    r"the corporation|staff)\b")
GENERIC = {"inc", "ltd", "limited", "llp", "corp", "corporation", "group", "planning", "homes", "properties",
           "holdings", "developments", "development", "associates", "consulting", "consultants", "the", "and"}
NUMBERED = re.compile(r"^\d|\b\d{6,7}\b|Ontario (?:Inc|Limited|Ltd)")
COMMON_FIRST = {"urban", "global", "north", "south", "east", "west", "new", "royal", "green", "first", "ontario",
                "canadian", "city", "park", "grand", "great", "metro", "united", "capital", "premier"}
SUFFIX_TOKENS = GENERIC | {"engineering", "communities", "realty", "builder", "builders", "of", "&"}


@dataclass
class Lead:
    organization: str
    councils: set = field(default_factory=set)
    meetings: set = field(default_factory=set)
    latest: str = ""
    evidence_url: str = ""
    evidence: str = ""

    @property
    def kind(self) -> str:
        n = self.organization.lower()
        if re.search(r"planning|consult|associates|engineering|architect|surveying|design|bousfields|llp", n):
            return "consultant"
        if re.search(r"\b(street|road|drive|boulevard|blvd|avenue|lane|line|sideroad|crescent)\b", n):
            return "site_company"  # single-site vehicle: find the parent before contacting
        return "builder"


def core(name: str) -> str:
    """Comparable key: lowercase words without corporate suffixes, '&'/'and' and punctuation."""
    words = re.findall(r"[a-z0-9]+", name.lower().replace("’", "'"))
    keep = [w for w in words if w not in SUFFIX_TOKENS]
    return " ".join(keep)


def clean(name: str) -> str | None:
    name = re.sub(r"\s+", " ", name).strip(" ,.-–")
    # trim leading words that aren't part of a firm name
    name = re.sub(r"^(?:The|A|An|By|From|For|And|Of)\s+(?=[A-Z])", "", name)
    if NUMBERED.search(name) or PUBLIC.search(name):
        return None
    key = core(name)
    if not key or len(key) < 3 or all(w in GENERIC for w in key.split()):
        return None
    if re.search(r"\.(pdf|docx?)\b", name, re.I):
        return None
    return name


def extract(text: str) -> list[tuple[str, str]]:
    """(organization, short evidence) pairs found within 90 characters after an application cue."""
    text = re.sub(r"\s+", " ", text)
    found = []
    for m in CUE.finditer(text):
        window = text[m.end(): m.end() + 90]
        n = NAME.match(window) or NAME.search(window[:45])
        if not n:
            continue
        org = clean(n.group(1))
        if org:
            # evidence is only the cue and the firm name: the repo is public, so no surrounding text
            # that could carry a private applicant's name
            found.append((org, f"{m.group(1)} {org}"))
    return found


def known_orgs(files=KNOWN_FILES) -> set[str]:
    keys = set()
    for f in files:
        if not Path(f).exists():
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for col in ("organization", "org", "email_or_domain", "email"):
                    v = (row.get(col) or "").strip()
                    if not v:
                        continue
                    if "@" in v or "." in v and " " not in v:
                        dom = v.split("@")[-1].split(".")[0]
                        if len(dom) > 3:
                            keys.add(dom.lower())
                    else:
                        v = re.sub(r"\(.*?\)", "", v)
                        if core(v):
                            keys.add(core(v))
    return keys


def is_known(org: str, known: set[str]) -> bool:
    k = core(org)
    squashed = k.replace(" ", "")
    for kn in known:
        if not kn:
            continue
        if k == kn or squashed == kn.replace(" ", ""):
            return True
        # first distinctive word match, e.g. "Jones Consulting Group Ltd." vs "The Jones Consulting Group"
        if k.split()[0] == kn.split()[0] and len(k.split()[0]) >= 3 and k.split()[0] not in COMMON_FIRST:
            return True
        if " " not in kn and len(kn) > 4 and squashed.startswith(kn):
            return True
    return False


def collect(feed: str = "housing", root: Path = EXCERPTS, known: set[str] | None = None) -> list[Lead]:
    known = known_orgs() if known is None else known
    leads: dict[str, Lead] = {}
    for f in sorted(root.glob(f"*/{feed}__*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for org, ev in extract(d.get("excerpt", "")):
            if is_known(org, known):
                continue
            key = core(org)
            lead = leads.get(key)
            if lead is None:
                lead = leads[key] = Lead(org)
            elif len(org) > len(lead.organization):
                lead.organization = org  # keep the fullest spelling ("... Group Inc." over "... Group")
            lead.councils.add(d.get("municipality", ""))
            lead.meetings.add((d.get("municipality", ""), d.get("meeting_date", ""), d.get("meeting_name", "")))
            date = d.get("meeting_date", "")
            if date >= lead.latest:
                lead.latest, lead.evidence_url, lead.evidence = date, d.get("url", ""), ev[:220]
    rank = {"consultant": 0, "builder": 1, "site_company": 2}
    return sorted(leads.values(), key=lambda l: (-len(l.councils), -len(l.meetings), rank[l.kind], l.organization))


def write(leads: list[Lead], path: Path = OUT, feed: str = "housing") -> None:
    cols = ["feed", "organization", "kind", "councils", "meetings", "latest_meeting", "evidence_url", "evidence", "status"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for l in leads:
            w.writerow([feed, l.organization, l.kind, "; ".join(sorted(l.councils)), len(l.meetings), l.latest,
                        l.evidence_url, l.evidence, "needs_address"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--feed", default="housing")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--write", action="store_true", help=f"write {OUT.relative_to(ROOT)}")
    a = ap.parse_args(argv)
    leads = collect(a.feed)
    for l in leads[: a.top]:
        print(f"{len(l.councils)} councils / {len(l.meetings)} meetings  {l.kind:10} {l.organization}  "
              f"[{'; '.join(sorted(l.councils))}] latest {l.latest}")
    if a.write:
        write(leads, feed=a.feed)
        print(f"wrote {len(leads)} leads to {OUT.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
