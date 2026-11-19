"""Render samples/sample-issue.md into site/sample.html using the landing page's styles."""
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
md = (ROOT / "samples" / "sample-issue.md").read_text()
body = markdown.markdown(md)

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sample issue: Council Radar, Ontario energy projects</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--paper:#FFFFFF;--ink:#14284B;--text:#1F2D44;--muted:#52607A;--rule:#D5DCE5;--mist:#EEF3F8;--line:#2F6FB5}
body{margin:0;background:var(--mist);color:var(--text);font:400 1.0625rem/1.65 "Public Sans",system-ui,sans-serif}
main{max-width:44rem;margin:2rem auto 4rem;padding:2rem 2.25rem 2.5rem;background:#fff;border:1px solid var(--rule);border-radius:12px}
@media (max-width:700px){main{margin:0;border:0;border-radius:0;padding:1.5rem 1.25rem 3rem}}
a{color:var(--line)} a:focus-visible{outline:3px solid var(--line);outline-offset:3px}
.back{font-size:.95rem}
h1{font:700 2rem/1.15 "Public Sans",sans-serif;letter-spacing:-.02em;color:var(--ink);margin:1.5rem 0 .2rem}
h2{font:700 1.3rem/1.3 "Public Sans",sans-serif;color:var(--ink);margin:2.6rem 0 .4rem;padding-top:1.2rem;border-top:1px solid var(--rule)}
h3{font:600 1.1rem/1.4 "Public Sans",sans-serif;color:var(--ink);margin:1.6rem 0 .2rem}
h3+p em{color:var(--muted);font-style:normal;font-size:.9rem}
blockquote{margin:.8rem 0;padding:.2rem 0 .2rem 1rem;border-left:3px solid var(--line);font:400 1rem/1.55 "Public Sans",sans-serif;color:var(--muted);background:var(--mist)}
.cta{margin-top:2.5rem;padding:1.25rem 1.5rem;background:var(--mist);border-radius:10px}.cta p{margin:.3rem 0}
.btn{display:inline-block;background:var(--ink);color:#fff;text-decoration:none;font-weight:600;padding:.75rem 1.1rem;border-radius:6px;margin:.4rem 1rem .2rem 0}.btn:hover{background:#0d1c36;color:#fff}
hr{border:0;border-top:1px solid var(--rule);margin:2.5rem 0 1rem}
</style></head>
<body><main><a class="back" href="index.html">Back to Council Radar</a>
%s
<div class="cta"><p><strong>Want to see it for your own councils?</strong> <a href="brief.html">Preview your Monday email</a> for the municipalities your projects depend on.</p><p><strong>Get this every Monday.</strong> Council activity on energy projects from 150 Ontario councils, each item linked to its source.</p><p><a class="btn" href="https://buy.stripe.com/eVqaEZ3ZGbwjc1Qdm38Vi00">Subscribe for $59 a month</a> <a href="mailto:councilradaron@gmail.com?subject=Free%%20trial%%20issue">Get a free trial issue</a></p></div></main><script src="start.js"></script>
</body></html>"""

(ROOT / "site" / "sample.html").write_text(PAGE % body)
print("wrote site/sample.html")
