# Daily outreach task (weekdays, 1:37 pm Toronto)

Owner: Huxley Boivin. Sends from councilradaron@gmail.com, signed as Huxley Boivin.
Files: `outreach/prospects.csv` (research list), `outreach/log.csv` (every email sent),
`outreach/suppression.csv` (never contact), `outreach/emails.md` (templates A, B, C and the follow-up).

## Hard limits
- At most **20 new prospects** and **20 follow-ups** per run. These are ceilings, not targets: never pad the list. One initial email and at most one
  follow-up per person, ever. Never more than one person per organization per run.
- Only email an address that the person or company **publishes themselves** (company contact page,
  team or bio page, press release, the author line on their own publication). Never guess or
  construct an address from a pattern, and never use data brokers or lead databases.
  Record the page in `address_source_url`.
- Skip any page that says it doesn't accept unsolicited commercial email. Skip personal (non-business)
  addresses, government and municipal staff, councillors, and residents' groups.
- Skip inboxes meant for something other than business inquiries: media, press, communications,
  investor relations, community engagement or project-feedback addresses (for example media@,
  press@, communication@, ir@, communityengagement@). Press releases are fine as a source of facts,
  but not as a source of addresses unless the address is listed for business or sales inquiries.
  Also skip individual contacts that only appear in regulatory or securities filings (OEB, SEC, SEDAR).
- Check for bounces again at the end of the run, after sending, and add any to `suppression.csv`.
- Never contact anyone in `suppression.csv` (matching email or domain) or anyone already in
  `log.csv` with stage `initial`, except for that one follow-up.
- Every claim in an email must be true and checkable: the project or publication you mention needs
  a source URL (`personalization_source_url`). Don't invent familiarity, mutual contacts or results.
- Every email ends with: `Council Radar · 230 Regina Street North, Waterloo, ON` and
  `If you'd rather not hear from me again, just reply "no thanks" and I won't follow up.`
- **Stop sending immediately** and notify the owner if: 2 or more bounces in this run or the last
  one, any Gmail warning, rate-limit or suspension notice, or any complaint.

## Steps
1. `git pull`. Read `log.csv` and `suppression.csv`.
2. **Replies first.** Search Gmail (`-in:sent newer_than:14d`) for replies from anyone in `log.csv`,
   and for bounces (`from:mailer-daemon OR subject:"Delivery Status Notification"`).
   - "no thanks", unsubscribe, stop, not interested, any negative reply: add to `suppression.csv`
     and set their log status to `opted_out`. Don't reply.
   - Bounce: status `bounced`, add to suppression.
   - Out-of-office: note it, and push the follow-up past their return date.
   - Interested, asking a question, or wanting a trial: status `replied`. **Don't answer**; tell the
     owner (they reply personally). A trial request also goes through the weekly task's trial path.
3. **Follow-ups.** For each `initial` sent 7 or more days ago with no reply (and not out of office),
   send the follow-up template as a reply in the same thread (`replyThreadId` = `thread_id`), mentioning one real item from the latest
   issue in `data/issues/`. Log stage `followup`.
4. **Find new prospects** until there are 20 good ones (fewer is fine; never pad the list):
   - Proponents and consultants named in this week's findings and pending excerpts
     (`data/issues/*-findings.json`, `python -m radar pending --feed energy --since <last week>`),
     e.g. a developer seeking a municipal support confirmation or presenting to council.
   - New IESO procurement results and qualified-applicant lists, and Ontario energy trade news
     (energy-storage.news, pv-magazine, Renewables Now, North American Windpower, Daily Commercial News)
     from the last month.
   - The unused rows of `outreach/prospects.csv`.
   Standing approvals: read `ops/approvals.md`. Law and consulting groups and large developers may get template E (enterprise pilot) instead of B.
   Priority: developers with an active Ontario project needing municipal support (template A) >
   law and consulting energy groups (B) > associations (C, at most 1 a month).
   **Housing edition (since 2026-11-24):** also prospect homebuilders, land developers, planning consultancies and
   land-use law groups named as applicants, agents or counsel in `python -m radar pending --feed housing` and
   `data/issues/*-housing-findings.json` (template H), using only addresses they publish for business contact. Same hard
   limits; housing and energy sends share the 20-per-run ceiling. Buyer types and examples: `ops/expansion/2026-11-23-housing-buyers.md`.
   **Start from `outreach/agenda_leads.csv` (since 2026-11-27).** `python tools/agenda_leads.py --write` ranks the firms
   named next to "submitted by / Agent: / Applicant: / on behalf of" in our housing excerpts (corporate names only,
   already-contacted orgs dropped). Each row has the agenda URL to use as `personalization_source_url`. It never
   contains addresses: a row with `status=needs_address` still needs one the firm publishes itself. When the address is
   found (here, or by the browser desk), set the row's `status` to `address_found <email> <source url>` and add the firm
   to `prospects.csv`; when none is published, set `no_published_address`. Prefer `consultant` rows (one consultancy
   files at many councils); find the parent company before emailing a `site_company` row.
   Add new organizations to `prospects.csv` with an evidence URL.
5. **Check, then send.** Before each email run
   `python tools/outreach_check.py --email <address> --org "<organization>" --source <address_source_url> [--stage followup] [--municipality "<council>"]`.
   It enforces the hard limits above (role inboxes, personal/government domains, filing sources, suppression,
   one initial and one follow-up). If it prints `DO NOT SEND`, don't send. If it warns that the prospect's council
   is not read, use the sample link, not a preview link, and don't imply we track that council.
   Send one email per prospect from `emails.md`, filling every bracket with real, sourced details.
   **No URLs or bare domains in initial emails or follow-ups** (since 2026-11-23; the Gmail connector wraps every
   link in a google.com/url redirect, see `ops/gmail_link_wrapping.md`). Templates offer the preview or sample
   on request ("reply 'preview'"). Still check the prospect's preview resolves before sending Template A:
   `https://getcouncilradar.ca/brief.html?for=<Company>&c=<municipality>[,<municipality>]` (`c` takes the short
   municipality name or the full slug), and record it in the `notes` column of log.csv so the chief of staff can send it
   when they reply. Templates B and C point to the sample, https://getcouncilradar.ca/sample.html, on request.
   Plain text, no attachments, no tracking. Log each send in `log.csv`, including the Gmail `thread_id`.
6. Commit `outreach/` and push (rebase first).
7. **Notify the owner** (push notification and one email to councilradaron@gmail.com) only if something was sent or needs them: new emails sent
   (organization, person, why), follow-ups sent, replies needing them, opt-outs, bounces, and anything
   that made you stop.
