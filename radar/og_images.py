"""Share-card images (1200x630 PNG) for links posted on LinkedIn, Bluesky, Reddit, Slack, email...

Built on every deploy into site/og/ (gitignored): one per council page, plus the homepage, sample,
tracker, preview and council directory. Uses Public Sans (SIL Open Font License, assets/fonts/).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

W, H = 1200, 630
INK = (20, 40, 75)
WHITE = (255, 255, 255)
SOFT = (201, 212, 230)
DIM = (143, 163, 195)
GREEN_BG, GREEN_FG = (221, 241, 228), (29, 92, 56)
GRAY_BG, GRAY_FG = (231, 235, 241), (63, 75, 96)
GOLD = (255, 229, 138)
FONTS = config.ROOT / "assets" / "fonts"
_cache: dict = {}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    key = (weight, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(str(FONTS / f"PublicSans-{weight}.ttf"), size)
    return _cache[key]


def _wrap(draw, text: str, weight: str, size: int, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=_font(weight, size)) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def _fit(draw, text: str, weight: str, width: int, max_lines: int, sizes=(84, 76, 68, 60, 54, 48, 42)) -> tuple[int, list[str]]:
    for size in sizes:
        lines = _wrap(draw, text, weight, size, width)
        if len(lines) <= max_lines and all(draw.textlength(l, font=_font(weight, size)) <= width for l in lines):
            return size, lines
    size = sizes[-1]
    return size, _wrap(draw, text, weight, size, width)[:max_lines]


def _radar(img: Image.Image) -> None:
    """Concentric rings and a sweep in the top-right corner, the brand mark at poster scale."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = W - 120, 110
    for r, a in ((520, 22), (400, 30), (280, 40), (160, 55)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(143, 163, 195, a), width=3)
    d.pieslice((cx - 520, cy - 520, cx + 520, cy + 520), 95, 140, fill=(143, 163, 195, 26))
    d.line((cx, cy, cx - 360, cy + 380), fill=(143, 163, 195, 70), width=4)
    img.alpha_composite(layer)


def _logo(d: ImageDraw.ImageDraw, x: int, y: int) -> None:
    d.ellipse((x, y, x + 44, y + 44), outline=WHITE, width=4)
    d.ellipse((x + 12, y + 12, x + 32, y + 32), outline=(127, 176, 230), width=4)
    d.line((x + 22, y + 22, x + 39, y + 10), fill=WHITE, width=4)
    d.text((x + 60, y + 4), "Council Radar", font=_font("Bold", 32), fill=WHITE)


def card(path: Path, title: str, subtitle: str = "", stats: list[tuple[str, str]] | None = None,
         badge: tuple[str, bool] | None = None, footer: str = "", note: str = "") -> Path:
    img = Image.new("RGBA", (W, H), INK + (255,))
    _radar(img)
    d = ImageDraw.Draw(img)
    x = 72
    _logo(d, x, 56)
    if badge:
        text, on = badge
        f = _font("Bold", 22)
        tw = d.textlength(text.upper(), font=f)
        bx = W - 72 - tw - 32
        d.rounded_rectangle((bx, 60, W - 72, 100), radius=8, fill=GREEN_BG if on else GRAY_BG)
        d.text((bx + 16, 68), text.upper(), font=f, fill=GREEN_FG if on else GRAY_FG)

    # Layout zones: title block from y=150, stats row at y=376 (104 high), note at 506, footer at 562.
    top, limit = 150, (352 if stats else (480 if note else 530))
    chosen = None
    for t_size in (84, 76, 68, 60, 54, 48, 42):
        t_lines = _wrap(d, title, "Bold", t_size, W - 2 * x)
        if len(t_lines) > 2 or any(d.textlength(l, font=_font("Bold", t_size)) > W - 2 * x for l in t_lines):
            continue
        for s_size in ((40, 36, 32, 28) if subtitle else (0,)):
            s_lines = _wrap(d, subtitle, "Medium", s_size, W - 2 * x) if subtitle else []
            hgt = len(t_lines) * int(t_size * 1.12) + (8 + len(s_lines) * int(s_size * 1.3) if s_lines else 0)
            if len(s_lines) <= 2 and top + hgt <= limit:
                chosen = (t_size, t_lines, s_size, s_lines)
                break
        if chosen:
            break
    if not chosen:  # last resort: smallest sizes, truncated
        chosen = (42, _wrap(d, title, "Bold", 42, W - 2 * x)[:2], 28, _wrap(d, subtitle, "Medium", 28, W - 2 * x)[:1] if subtitle else [])
    t_size, t_lines, s_size, s_lines = chosen
    y = top
    for line in t_lines:
        d.text((x, y), line, font=_font("Bold", t_size), fill=WHITE)
        y += int(t_size * 1.12)
    if s_lines:
        y += 8
        for line in s_lines:
            d.text((x, y), line, font=_font("Medium", s_size), fill=SOFT)
            y += int(s_size * 1.3)

    if stats:
        y, sx = 376, x
        fn, fl = _font("Bold", 48), _font("Medium", 23)
        for num, label in stats[:3]:
            wbox = max(d.textlength(num, font=fn), d.textlength(label, font=fl)) + 48
            d.rounded_rectangle((sx, y, sx + wbox, y + 104), radius=14, fill=(33, 55, 92), outline=(74, 97, 135), width=2)
            d.text((sx + 24, y + 10), num, font=fn, fill=GOLD if label.startswith("subscriber") else WHITE)
            d.text((sx + 24, y + 66), label, font=fl, fill=SOFT)
            sx += wbox + 16

    if note:
        d.text((x, 506), note, font=_font("SemiBold", 26), fill=WHITE)
    d.text((x, 562), footer or "huxleyboivin.github.io/council-radar", font=_font("Medium", 24), fill=DIM)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, "PNG", optimize=True)
    return path


def write_all(index: dict, upcoming: dict, slug, when, out_dir: Path | None = None) -> int:
    """Cards for every council page plus the site's main pages. Returns how many were written."""
    out_dir = out_dir or (config.ROOT / "site" / "og")
    meta = index["meta"]
    month = meta.get("month", {})
    n = 0
    card(out_dir / "home.png", "Where does your council stand on energy projects?",
         f"{meta.get('covered', 150)} Ontario councils read every morning. What matters, every Monday.",
         [(str(meta.get("covered", 150)), "councils read daily"),
          (f"{month.get('meetings', 0):,}", "meetings, last 30 days"),
          ("Free", "first issue")], ("Read every morning", True)); n += 1
    card(out_dir / "councils.png", "Ontario councils and energy projects",
         "Decisions, early signals and next meetings for every council we read.",
         [(str(meta.get("covered", 150)), "council pages"), ("Daily", "agendas read"), ("Free", "calendar feeds")]); n += 1
    card(out_dir / "sample.png", "Council Radar: a sample Monday email",
         "Support requests, decisions, new rules and zoning changes on solar, wind, battery storage and gas projects.",
         note="Every item links to the council's own document."); n += 1
    card(out_dir / "tracker.png", "Ontario municipal support tracker",
         "Which councils gave or refused support for IESO energy projects, and which adopted new rules. Free and sourced.",
         note=f"{meta.get('covered', 150)} councils monitored"); n += 1
    card(out_dir / "brief.png", "Your Monday email, previewed",
         "See what Council Radar would send you for the councils your projects depend on.",
         note="Pick your councils. It updates as you go."); n += 1
    for c in index["councils"]:
        if not (c.get("c") or c.get("i")):
            continue
        items, locked, covered = c.get("i") or [], c.get("l", 0), bool(c.get("c"))
        stats = [(str(len(items)), "public " + ("item" if len(items) == 1 else "items"))] if items or not covered else \
                [(f"{c.get('d', 0):,}", "documents read")]
        if locked:
            stats.append((str(locked), "subscriber " + ("item" if locked == 1 else "items")))
        if covered:
            stats.append((str(c.get("k", 0)), "meetings, last 30 days"))
        nxt = (upcoming.get(c["n"]) or [None])[0]
        note = f"Next: {nxt[0]}, {when(nxt[1])}" if nxt else ""
        if len(note) > 64:
            note = note[:61].rstrip() + "…"
        card(out_dir / "councils" / f"{slug(c['n'])}.png", c["n"], "and energy projects", stats,
             ("Read every morning" if covered else "Not read yet", covered), note=note)
        n += 1
    return n
