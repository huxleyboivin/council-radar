"""Pre-send check for outreach emails, so the hard rules in ops/outreach_task.md are enforced by code.

Why: in the first week, 3 of 22 sends went to media/communications inboxes (one bounced), one
address came from an SEC filing, and the best developer prospects (Boralex in Greater Napanee,
Kruger in Prince Edward County) were skipped because their councils are not read. This tool
answers, before each send: may we email this address, and does the prospect's council have a
real preview?

Usage:
  python tools/outreach_check.py --email a@b.com --org "Acme" --source https://acme.com/contact \
      [--municipality "Greater Napanee"]
  python tools/outreach_check.py --audit        # re-check every row already in outreach/log.csv
  python tools/outreach_check.py --coverage "Prince Edward"

Exit code 1 if any BLOCK problem is found (WARN problems don't fail).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "outreach" / "log.csv"
SUPPRESSION = ROOT / "outreach" / "suppression.csv"

# Inboxes the rules say to skip: media, press, communications, IR, community/project feedback.
ROLE_PREFIXES = (
    "media", "press", "news", "communication", "communications", "comms", "pr", "ir", "investor",
    "investors", "investorrelations", "communityengagement", "community", "engagement", "feedback",
    "projectfeedback", "noreply", "no-reply", "donotreply", "careers", "jobs", "hr", "privacy",
    "accessibility", "complaints", "webmaster",
)
PERSONAL_DOMAINS = {
    "gmail.com", "googlemail.com", "hotmail.com", "outlook.com", "live.com", "yahoo.com", "yahoo.ca",
    "icloud.com", "me.com", "aol.com", "rogers.com", "sympatico.ca", "bell.net", "shaw.ca",
    "telus.net", "cogeco.ca", "protonmail.com", "proton.me",
}
# Government and municipal addresses are off limits.
GOV_DOMAIN = re.compile(r"(\.gc\.ca|\.gov\.on\.ca|ontario\.ca|\.gov|\.on\.ca|ieso\.ca|oeb\.ca)$")
GOV_NAME = re.compile(r"^(town|township|city|county|municipality|village|region)of", re.I)
# Addresses found only in regulatory or securities filings are off limits.
FILING_HOSTS = ("sec.gov", "sedarplus.ca", "sedar.com", "oeb.ca", "rds.oeb.ca", "sedi.ca")


@dataclass
class Problem:
    level: str  # BLOCK or WARN
    message: str

    def __str__(self):
        return f"{self.level}: {self.message}"


def _norm(s: str) -> str:
    s = "".join(ch for ch in unicodedata.normalize("NFD", s or "") if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


_ORG_NOISE = re.compile(r"\b(inc|ltd|llp|lp|corp|corporation|co|company|canada|ontario|limited|group|the)\b")


def org_key(org: str) -> str:
    """'Blake, Cassels & Graydon LLP (energy group)' and 'Blake Cassels & Graydon' -> same key."""
    s = re.sub(r"\(.*?\)", " ", org or "")
    return re.sub(r"\s+", " ", _ORG_NOISE.sub(" ", _norm(s))).strip()


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def domain_of(email: str) -> str:
    return email.rsplit("@", 1)[-1].strip().lower()


def check_address(email: str, org: str = "", source_url: str = "",
                  log_rows: list[dict] | None = None, suppression_rows: list[dict] | None = None,
                  stage: str = "initial", exclude_row: dict | None = None) -> list[Problem]:
    """Every problem with sending `stage` email to `email`. Empty list means OK to send."""
    log_rows = _read_csv(LOG) if log_rows is None else log_rows
    suppression_rows = _read_csv(SUPPRESSION) if suppression_rows is None else suppression_rows
    problems: list[Problem] = []
    email = (email or "").strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email, re.I):
        return [Problem("BLOCK", f"not a valid address: {email!r}")]
    local, dom = email.lower().split("@", 1)

    first = re.split(r"[._+\-]", local)[0]
    if local in ROLE_PREFIXES or first in ROLE_PREFIXES:
        problems.append(Problem("BLOCK", f"{local}@ is a media/communications/IR-type inbox, not a business-inquiry address"))
    if dom in PERSONAL_DOMAINS:
        problems.append(Problem("BLOCK", f"{dom} is a personal email provider"))
    if GOV_DOMAIN.search(dom) or GOV_NAME.match(dom.replace("-", "")):
        problems.append(Problem("BLOCK", f"{dom} looks like a government or municipal domain"))

    for row in suppression_rows:
        entry = (row.get("email_or_domain") or "").strip().lower()
        if not entry:
            continue
        if entry == email.lower() or ("@" not in entry and (dom == entry or dom.endswith("." + entry))):
            problems.append(Problem("BLOCK", f"suppressed ({row.get('reason', '').strip() or 'no reason given'})"))
            break

    if not source_url:
        problems.append(Problem("BLOCK", "no address_source_url: record the page where the address is published"))
    else:
        host = urlparse(source_url).netloc.lower()
        if any(host == h or host.endswith("." + h) for h in FILING_HOSTS):
            problems.append(Problem("BLOCK", f"address source is a regulatory/securities filing ({host})"))
        elif host.endswith(("globenewswire.com", "newswire.ca", "prnewswire.com", "businesswire.com")):
            problems.append(Problem("WARN", "address comes from a press release: only OK if it is listed for business or sales inquiries"))
        elif dom.split(".")[-2:] != host.split(".")[-2:] and not host.endswith(dom):
            problems.append(Problem("WARN", f"address domain {dom} differs from the source page {host}: make sure the company publishes it"))

    key = org_key(org)
    for row in log_rows:
        if exclude_row is not None and row is exclude_row:
            continue
        same_person = (row.get("email") or "").strip().lower() == email.lower()
        same_org = key and org_key(row.get("organization", "")) == key
        same_domain = domain_of(row.get("email", "")) == dom
        if same_person and row.get("stage") == stage:
            problems.append(Problem("BLOCK", f"already sent a {stage} email to {email} on {row.get('date')}"))
        elif stage == "initial" and same_person:
            problems.append(Problem("BLOCK", f"{email} already contacted on {row.get('date')} ({row.get('stage')})"))
        elif stage == "initial" and (same_org or same_domain) and not same_person:
            problems.append(Problem("WARN", f"{row.get('organization')} already contacted on {row.get('date')} "
                                            f"({row.get('email')}): one person per organization per run, and don't double up"))
        if same_person and (row.get("status") or "") in ("opted_out", "bounced"):
            problems.append(Problem("BLOCK", f"{email} is {row.get('status')}"))
    return _dedupe(problems)


def _dedupe(problems: list[Problem]) -> list[Problem]:
    seen, out = set(), []
    for p in problems:
        if str(p) not in seen:
            seen.add(str(p))
            out.append(p)
    return out


# --- coverage -----------------------------------------------------------------------------

def load_coverage(root: Path = ROOT) -> dict[str, dict]:
    """Municipality name -> {"name", "status": "read" | "civicweb" | "unknown", "slug"}."""
    out: dict[str, dict] = {}
    txt = root / "data" / "ontario_municipalities.txt"
    if txt.exists():
        for line in txt.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*([^#].*?)\s*\((\w[\w ]*)\)\s*$", line)
            if m:
                name = f"{m.group(2)} of {m.group(1)}"
                out[name] = {"name": name, "status": "unknown", "slug": None}

    def load(p):
        return yaml.safe_load(p.read_text(encoding="utf-8")) or [] if p.exists() else []

    for row in load(root / "data" / "platform_survey.yaml"):
        out[row["name"]] = {"name": row["name"], "status": row.get("platform", "other"), "slug": row.get("slug")}
    for p in (root / "municipalities.yaml", root / "data" / "discovered.yaml"):
        for row in load(p):
            out[row["name"]] = {"name": row["name"], "status": "read", "slug": row.get("slug")}
    return out


_KIND = re.compile(r"^(the )?(town|township|city|county|municipality|village|region|united counties|regional municipality) of ")


def _bare(name: str) -> str:
    s = _norm(name)
    s = _KIND.sub("", s + " ").strip() if _KIND.match(s + " ") else s
    s = re.sub(r"\b(county|township|municipality|town|city|village)$", "", s).strip()
    return s


def find_council(query: str, coverage: dict[str, dict] | None = None) -> list[dict]:
    """Councils matching a loose name ('Napanee', 'Prince Edward County', 'minto')."""
    coverage = load_coverage() if coverage is None else coverage
    q = _bare(query)
    if not q:
        return []
    hits = [v for k, v in coverage.items() if _bare(k) == q or _norm(k) == _norm(query)]
    if not hits:
        hits = [v for k, v in coverage.items() if re.search(r"\b" + re.escape(q) + r"\b", _norm(k))]
    # 'County of Haldimand' (from the master list) and 'Haldimand County' (read) are one council:
    # keep the entry that knows the most.
    rank = {"read": 0, "civicweb": 1}
    best: dict[str, dict] = {}
    for h in hits:
        k = _bare(h["name"]) + "|" + (_KIND.match(_norm(h["name"]) + " ").group(2) if _KIND.match(_norm(h["name"]) + " ")
                                       else (_norm(h["name"]).split()[-1] if _norm(h["name"]) else ""))
        if k not in best or rank.get(h["status"], 9) < rank.get(best[k]["status"], 9):
            best[k] = h
    return list(best.values())


def coverage_advice(query: str, coverage: dict[str, dict] | None = None) -> list[Problem]:
    hits = find_council(query, coverage)
    if not hits:
        return [Problem("WARN", f"no Ontario council matches {query!r}: check the spelling")]
    out = []
    for h in hits:
        if h["status"] == "read":
            continue
        why = ("its CiviCweb portal disallows bots in robots.txt" if h["status"] == "civicweb"
               else "we have no reader for its agenda platform yet")
        out.append(Problem("WARN", f"{h['name']} is not read ({why}). A preview link would show 'not read yet': "
                                   "use the sample link and don't imply we track this council"))
    return out


def audit(log_rows: list[dict] | None = None, suppression_rows: list[dict] | None = None) -> list[tuple[dict, list[Problem]]]:
    """Re-check rows already sent, ignoring the row itself. Used for the weekly review."""
    log_rows = _read_csv(LOG) if log_rows is None else log_rows
    suppression_rows = _read_csv(SUPPRESSION) if suppression_rows is None else suppression_rows
    results = []
    for row in log_rows:
        if row.get("stage") != "initial":
            continue
        earlier = [r for r in log_rows if r is not row and r.get("date", "") < row.get("date", "")]
        # Suppression entries added *because of* this send would always match; skip those.
        sup = [s for s in suppression_rows if (s.get("email_or_domain") or "").lower() != row.get("email", "").lower()]
        probs = [p for p in check_address(row.get("email", ""), row.get("organization", ""),
                                          row.get("address_source_url", ""), earlier, sup)
                 if p.level == "BLOCK"]
        if probs:
            results.append((row, probs))
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email")
    ap.add_argument("--org", default="")
    ap.add_argument("--source", default="", help="address_source_url")
    ap.add_argument("--stage", default="initial", choices=["initial", "followup"])
    ap.add_argument("--municipality", action="append", default=[])
    ap.add_argument("--coverage", action="append", default=[], help="only report whether a council is read")
    ap.add_argument("--audit", action="store_true")
    a = ap.parse_args(argv)

    problems: list[Problem] = []
    if a.audit:
        res = audit()
        for row, probs in res:
            print(f"{row['date']} {row['email']} ({row['organization']}):")
            for p in probs:
                print("   ", p)
        print(f"{len(res)} sent row(s) would now be blocked")
        return 0
    for q in a.coverage:
        for h in find_council(q) or [{"name": q, "status": "unknown"}]:
            print(f"{h['name']}: {h['status']}")
        return 0
    if not a.email:
        ap.error("--email, --audit or --coverage is required")
    problems += check_address(a.email, a.org, a.source, stage=a.stage)
    for m in a.municipality:
        problems += coverage_advice(m)
    for p in problems:
        print(p)
    blocked = any(p.level == "BLOCK" for p in problems)
    print("DO NOT SEND" if blocked else ("OK to send (read the warnings)" if problems else "OK to send"))
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
