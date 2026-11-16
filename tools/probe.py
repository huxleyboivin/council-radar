"""Fetch a few URLs politely and print what came back (for building new portal parsers)."""
import re
import sys
import time

import requests

UA = "CouncilRadarBot/1.0 (+https://huxleyboivin.github.io/council-radar/; councilradaron@gmail.com)"
s = requests.Session()
s.headers["User-Agent"] = UA
for url in sys.argv[1:]:
    time.sleep(1.5)
    try:
        r = s.get(url, timeout=25)
    except Exception as e:
        print("=" * 80, "\n", url, "ERR", e)
        continue
    print("=" * 80)
    print(url, r.status_code, r.headers.get("content-type"), len(r.content), "final:", r.url)
    body = r.text
    if "json" in (r.headers.get("content-type") or ""):
        print(body[:3000])
        continue
    links = sorted(set(re.findall(r'href="([^"]+)"', body)))
    print("LINKS", len(links))
    for l in links[:120]:
        print("  ", l)
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    print("TEXT", re.sub(r"\s+", " ", text)[:2500])
    for m in re.findall(r"(?:url|ajax|fetch|\.svc|api)[^\n]{0,160}", body, flags=re.I)[:25]:
        print("  JS:", m.strip()[:200])
