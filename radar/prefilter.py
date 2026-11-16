"""Cheap keyword pass: cut each document down to the passages a feed could care about."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import config

WINDOW = 1500        # characters of context on each side of a hit
MAX_CHARS = 14000    # cap on text sent to the model per document per feed


@dataclass
class Feed:
    key: str
    title: str
    audience: str
    patterns: list[re.Pattern]
    categories: list[str]
    enabled: bool = True


def load_feeds(path: Path | None = None) -> dict[str, Feed]:
    raw = yaml.safe_load((path or config.ROOT / "feeds.yaml").read_text())
    feeds = {}
    for key, f in raw.items():
        feeds[key] = Feed(
            key=key,
            title=f["title"],
            audience=" ".join(str(f.get("audience", "")).split()),
            patterns=[re.compile(p, re.I) for p in f["patterns"]],
            categories=list(f.get("categories", [])),
            enabled=bool(f.get("enabled", True)),
        )
    return feeds


def excerpt(text: str, feed: Feed) -> tuple[int, str]:
    """Return (hit_count, merged context windows) for a document; ("", 0) if nothing matches."""
    spans = []
    for p in feed.patterns:
        for m in p.finditer(text):
            spans.append((max(0, m.start() - WINDOW), min(len(text), m.end() + WINDOW)))
    if not spans:
        return 0, ""
    spans.sort()
    merged = [list(spans[0])]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    parts, total = [], 0
    for s, e in merged:
        chunk = text[s:e]
        if total + len(chunk) > MAX_CHARS:
            chunk = chunk[: MAX_CHARS - total]
        parts.append(chunk)
        total += len(chunk)
        if total >= MAX_CHARS:
            break
    return len(spans), "\n...\n".join(parts)
