"""Diagnostic: fetch a few recent agenda pages and show how much text they hold and what
energy-ish words appear. Read-only; uses the same polite Fetcher as the daily job."""
import re
import sys
from datetime import date, timedelta

from radar import escribe, prefilter

BROAD = re.compile(r"energy|battery|solar|wind|IESO|storage|electricity|hydro one|generation|"
                   r"renewable|BESS|LT2|municipal support", re.I)
feed = prefilter.load_feeds()["energy"]
f = escribe.Fetcher()
today = date.today()
for slug in sys.argv[1:]:
    print("=" * 70, "\n", slug)
    try:
        ms = escribe.list_meetings(f, slug, today - timedelta(days=21), today + timedelta(days=14))
    except Exception as e:
        print("  list error", repr(e)[:200]); continue
    ms = [m for m in ms if m.has_agenda][:4]
    for m in ms:
        try:
            for key, title, url, text in escribe.iter_meeting_documents(f, slug, m):
                hits, _ = prefilter.excerpt(text or "", feed)
                broad = sorted({w.group(0).lower() for w in BROAD.finditer(text or "")})
                print(f"  {m.start} | {title[:60]} | chars={len(text or '')} feed_hits={hits} broad={broad[:12]}")
                print("     url:", url)
                print("     head:", re.sub(r"\s+", " ", (text or ""))[:300])
                lines = [l for l in (text or "").splitlines() if BROAD.search(l)][:5]
                for l in lines:
                    print("     >", l[:200])
        except Exception as e:
            print("  meeting error", m.url, repr(e)[:200])
