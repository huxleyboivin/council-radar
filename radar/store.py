"""SQLite store, committed back to the repo by the GitHub Actions workflow."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS meetings (
  meeting_id TEXT PRIMARY KEY, municipality TEXT, slug TEXT, name TEXT,
  start TEXT, url TEXT, seen_at TEXT
);
CREATE TABLE IF NOT EXISTS documents (
  doc_key TEXT PRIMARY KEY, meeting_id TEXT, title TEXT, url TEXT,
  text_hash TEXT, fetched_at TEXT, status TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS reads (
  doc_key TEXT, feed TEXT, text_hash TEXT, hits INTEGER, read_at TEXT,
  PRIMARY KEY (doc_key, feed)
);
CREATE TABLE IF NOT EXISTS findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feed TEXT, doc_key TEXT, municipality TEXT, meeting_name TEXT, meeting_date TEXT,
  category TEXT, headline TEXT, project TEXT, proponent TEXT, technology TEXT,
  capacity_mw REAL, status TEXT, summary TEXT, evidence TEXT, source_url TEXT,
  confidence REAL, fingerprint TEXT UNIQUE, created_at TEXT, issue_id TEXT
);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, started_at TEXT, finished_at TEXT, stats TEXT
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:20]


def connect(path: Path | None = None) -> sqlite3.Connection:
    p = Path(path or config.DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def upsert_meeting(con, m, municipality: str, slug: str):
    con.execute(
        "INSERT INTO meetings VALUES (?,?,?,?,?,?,?) ON CONFLICT(meeting_id) DO UPDATE SET "
        "name=excluded.name, start=excluded.start, url=excluded.url",
        (m.meeting_id, municipality, slug, m.name, m.start.isoformat() if m.start else None, m.url, now()),
    )


def doc_status(con, doc_key: str):
    return con.execute("SELECT * FROM documents WHERE doc_key=?", (doc_key,)).fetchone()


def save_document(con, doc_key, meeting_id, title, url, text_hash, status="ok", error=None):
    con.execute(
        "INSERT INTO documents VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(doc_key) DO UPDATE SET "
        "text_hash=excluded.text_hash, fetched_at=excluded.fetched_at, status=excluded.status, error=excluded.error",
        (doc_key, meeting_id, title, url, text_hash, now(), status, error),
    )


def already_read(con, doc_key: str, feed: str, text_hash: str) -> bool:
    r = con.execute("SELECT text_hash FROM reads WHERE doc_key=? AND feed=?", (doc_key, feed)).fetchone()
    return bool(r and r["text_hash"] == text_hash)


def mark_read(con, doc_key, feed, text_hash, hits):
    con.execute("INSERT OR REPLACE INTO reads VALUES (?,?,?,?,?)", (doc_key, feed, text_hash, hits, now()))


def fingerprint(feed: str, f: dict) -> str:
    key = "|".join(str(f.get(k, "")).lower().strip() for k in
                   ("municipality", "meeting_date", "category", "project", "headline"))
    return sha(feed + "|" + key)


def save_finding(con, feed: str, f: dict) -> bool:
    try:
        con.execute(
            "INSERT INTO findings (feed, doc_key, municipality, meeting_name, meeting_date, category, headline, "
            "project, proponent, technology, capacity_mw, status, summary, evidence, source_url, confidence, "
            "fingerprint, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (feed, f.get("doc_key"), f.get("municipality"), f.get("meeting_name"), f.get("meeting_date"),
             f.get("category"), f.get("headline"), f.get("project"), f.get("proponent"), f.get("technology"),
             f.get("capacity_mw"), f.get("status"), f.get("summary"), f.get("evidence"), f.get("source_url"),
             f.get("confidence"), fingerprint(feed, f), now()),
        )
        return True
    except sqlite3.IntegrityError:
        return False  # duplicate of something already recorded


def unsent_findings(con, feed: str, min_confidence: float = 0.5):
    return con.execute(
        "SELECT * FROM findings WHERE feed=? AND issue_id IS NULL AND COALESCE(confidence,1)>=? "
        "ORDER BY meeting_date DESC, municipality", (feed, min_confidence)).fetchall()


def mark_sent(con, ids, issue_id: str):
    con.executemany("UPDATE findings SET issue_id=? WHERE id=?", [(issue_id, i) for i in ids])


def log_run(con, kind: str, started: str, stats: dict):
    con.execute("INSERT INTO runs (kind, started_at, finished_at, stats) VALUES (?,?,?,?)",
                (kind, started, now(), json.dumps(stats)))
