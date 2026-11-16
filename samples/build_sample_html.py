"""Render samples/sample-issue.md into site/sample.html using the landing page's styles."""
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
md = (ROOT / "samples" / "sample-issue.md").read_text()
body = markdown.markdown(md)

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sample issue · Council Radar: Ontario Energy Projects</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>
:root{--paper:#F6F7F4;--ink:#14284B;--muted:#4D5B73;--rule:#C9D0DA;--line:#2F6FB5}
body{margin:0;background:var(--paper);color:var(--ink);font:400 1.0625rem/1.65 "Public Sans",system-ui,sans-serif}
main{max-width:42rem;margin:0 auto;padding:2rem 1.5rem 4rem}
a{color:var(--line)} a:focus-visible{outline:3px solid var(--line);outline-offset:3px}
.back{font-size:.95rem}
h1{font:600 2.1rem/1.15 "Source Serif 4",Georgia,serif;margin:1.5rem 0 .2rem}
h2{font:600 1.35rem/1.3 "Source Serif 4",Georgia,serif;margin:2.6rem 0 .4rem;padding-top:1.2rem;border-top:2px solid var(--ink)}
h3{font:600 1.12rem/1.35 "Source Serif 4",Georgia,serif;margin:1.6rem 0 .2rem}
h3+p em{color:var(--muted);font-style:normal;font-size:.9rem}
blockquote{margin:.8rem 0;padding:.2rem 0 .2rem 1rem;border-left:3px solid var(--line);font:italic 400 1rem/1.55 "Source Serif 4",Georgia,serif;color:var(--muted)}
hr{border:0;border-top:1px solid var(--rule);margin:2.5rem 0 1rem}
</style></head>
<body><main><a class="back" href="index.html">Back to Council Radar</a>
%s
<p><a href="index.html#pricing">Subscribe for $59 a month</a></p></main></body></html>"""

(ROOT / "site" / "sample.html").write_text(PAGE % body)
print("wrote site/sample.html")
