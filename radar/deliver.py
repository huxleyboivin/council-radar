"""Deliver an issue through Buttondown (which also handles Stripe billing and unsubscribes)."""
from __future__ import annotations

import requests

from . import config

API = "https://api.buttondown.com/v1/emails"


def send(subject: str, body_markdown: str, mode: str | None = None, session=None) -> dict:
    """mode="draft" creates a draft to review in Buttondown; mode="send" sends to subscribers."""
    if not config.BUTTONDOWN_API_KEY:
        raise RuntimeError("BUTTONDOWN_API_KEY is not set")
    mode = mode or config.DELIVERY_MODE
    payload = {"subject": subject, "body": body_markdown,
               "status": "about_to_send" if mode == "send" else "draft"}
    s = session or requests
    r = s.post(API, json=payload, timeout=60,
               headers={"Authorization": f"Token {config.BUTTONDOWN_API_KEY}"})
    if r.status_code >= 400:
        raise RuntimeError(f"Buttondown error {r.status_code}: {r.text[:500]}")
    return r.json()
