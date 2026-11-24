# Buttondown migration (prepared 2026-11-24 by the chief of staff)

Why: the Gmail connector rewrites every link to google.com/url (`ops/gmail_link_wrapping.md`). Buttondown sends
plain links, adds its own unsubscribe, and keeps subscriber data out of this public repo.

## What's ready in the repo
- `radar/deliver.py`: pinned API version `2026-11-10`; `send_weekly()` sends one email per audience tag
  (`active`, `trial-1`, `trial-2`), filtered by tag ID, each with the CASL footer and, for trials, the
  "trial issue N of 2" line with both Stripe links (same text as `ops/weekly_task.md`). Sends set
  `X-Buttondown-Live-Dangerously` (required for `about_to_send` on API 2026-04-01+; the old `send()` would
  have failed with `sending_requires_confirmation`). `advance_trials()` moves readers trial-2 -> trial-ended,
  then trial-1 -> trial-2, and stops if Buttondown merges tags instead of replacing them.
- `python -m radar send-issue [--issue data/issues/<date>-energy.md] [--mode draft|send] [--dry-run]`.
  Writes `data/issues/<date>-energy.buttondown.json` (email IDs and counts only) and refuses to send the same
  issue twice.
- `.github/workflows/weekly.yml`: Mondays 9:11 a.m. Toronto, after the weekly task pushes the issue. Does
  nothing without the secret; skips if this week's issue isn't rendered; defaults to **draft** mode.
- Tests: `tests/test_deliver.py` (fake HTTP session, no network).
- Fixed: `radar digest --deliver` no longer marks findings sent when it only created a draft.

## Switch-over checklist (weekly business review owns this once the secret exists)
1. Huxley: free Buttondown account, API key added as the `BUTTONDOWN_API_KEY` Actions secret. (Reserved: account creation.)
2. In Buttondown, create tags `active`, `trial-1`, `trial-2`, `trial-ended` (tags need the Basic plan or
   higher per Buttondown's docs; if the free plan lacks tags, that's a spending decision for Huxley).
3. Import current active and trial readers from the subscriber sheet with their tag (Buttondown import, or
   the browser desk). Use type `regular` only for people who asked or paid, so nobody gets a surprise opt-in email.
4. Run the workflow by hand in draft mode; check the three drafts in Buttondown: footer, trial line, links plain.
5. Send a test to councilradaron@gmail.com; "Show original" should show plain getcouncilradar.ca links.
6. Update `ops/weekly_task.md` step 5: the weekly task renders and pushes, but no longer emails subscribers from
   Gmail (it only adds new trial readers to Buttondown). Then set the repo variable `RADAR_DELIVERY_MODE=send`.
   Do these two together, or readers get the issue twice.

## Still open
- New trial readers: the Claude tasks don't hold the API key. Options: Buttondown's public embed-subscribe
  form from the site's Start panel (tag `trial-1`; needs the Buttondown username), or the browser desk adds them.
- Confirm on the first live run whether `GET /v1/subscribers?tag=` takes the tag name or ID (the code passes the name).
