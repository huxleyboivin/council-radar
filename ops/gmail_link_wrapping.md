# Gmail connector rewrites every link (diagnosed 2026-11-23)

Found by the browser desk on 2026-11-23 ("Show original" on sent outreach), confirmed by the chief of staff
the same day with three test messages to councilradaron@gmail.com, read back with get_message format RAW
(the stored MIME, not a rendered read-back):

| test | what we sent | what Gmail stored and sent |
|---|---|---|
| send_message, plain body | `https://getcouncilradar.ca/sample.html` | `https://www.google.com/url?q=https://getcouncilradar.ca/sample.html&source=gmail&ust=...&sa=E` |
| send_message, plain body | `getcouncilradar.ca/sample.html` (no scheme) | wrapped the same way (as `http://...`) |
| send_message, htmlBody | `<a href="https://getcouncilradar.ca/sample.html">` and bare `getcouncilradar.ca` | both hrefs wrapped |
| create_draft | `https://getcouncilradar.ca/sample.html` | wrapped in the saved draft |

So the rewrite happens inside the Gmail connector at send/draft time. It is not caused by copying text from a
Gmail read-back, and nothing in this repo can prevent it. Writing links without a scheme, or as HTML anchors, does not help.

## What it affects
- Every outreach email, follow-up and reply sent by the scheduled tasks (28 so far), the weekly issue and
  preview emails, and the link-building drafts Huxley sends with one click (they are wrapped before he sees them).
- The `ust=` value is about 24 hours after sending. After that, clicking usually shows Google's
  "Redirect notice" page instead of going straight to the site. Wrapped google.com/url links can also look
  like phishing to corporate spam filters (law firms, utilities), which hurts deliverability.

## Options (decision for Huxley, because it changes how other agents send)
1. Send through Gmail's web UI instead of the connector: the browser desk composes and sends (or Huxley
   sends link-pitch drafts after retyping the link). Slower, evening only, but links stay plain.
2. Send link-free first emails: no URL in the body, offer "reply 'preview' and I'll send it". Replies
   from the connector would still be wrapped, so the preview link would have to go out by the browser desk.
3. Ask Anthropic support whether the connector's link rewriting can be turned off for this account.
4. Accept it for now (links still work, with an interstitial after ~24 h).

Recommended: 2 for cold email (also tends to help deliverability) plus 1 for anything with a link that matters
(trial confirmations, preview links, link pitches), and 3 in parallel.

## Decision (Huxley, 2026-11-23): options 2 + Buttondown + 3
- **Cold email is link-free** (templates A, B, C and the follow-up in `outreach/emails.md`). Prospects reply
  "preview"/"sample" and the chief of staff replies with the link. They click within the day, so the redirect still works.
- **Weekly issue and trial emails move to Buttondown** (`radar/deliver.py`, `weekly.yml` already support it) once
  Huxley creates a free Buttondown account and adds `BUTTONDOWN_API_KEY` as a GitHub Actions secret. Until then
  the weekly issue keeps sending through Gmail.
- **Huxley asks Anthropic support** whether the connector's link rewriting can be turned off.
- Gmail web sending through the browser desk is for one-off messages only (e.g. the CiviCweb request), not the standard path.
