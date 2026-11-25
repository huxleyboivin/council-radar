# Design log

The web designer agent (Wednesdays and Sundays) ships one bold, measured site change per run and records it here.
Read this first so changes build on each other instead of repeating. Earlier design work (survey-plan hero, Start panel,
calculator, council pages, share cards, photos and motion) is in `ops/improvements.md` and `ops/design-spec.md`.

## 2026-11-25: Housing gets a front door, and the Start panel learns which edition you want

**What changed**
- `site/housing.html` (built by `samples/build_housing_html.py`) was a plain document page. It now opens with:
  - **A "Development proposal" notice sign**, the vernacular of Ontario development (the boards posted on sites under
    application). It shows the sample's largest real projects (Markham 987 homes, Mississauga 144, Barrie 125), one
    board at a time behind tabs, with the applications, committee and date, file number and a link to the council's own
    document. Parsed from `samples/housing-sample.md`, so it changes when the sample does. Clearly labelled as from our
    sample, with no city branding.
  - **A housing council lookup**: type a municipality and see how many council and committee meetings had housing items
    (OPAs, rezonings, subdivisions, OLT and so on) in the last 30 days and on posted agendas, the three most recent meeting
    names and dates, and the next meeting. Counts and meeting names only, never the item content (that stays for
    subscribers). Councils we don't read get the concierge offer. Each lookup adds the council to a list; "Start free
    with N councils" opens the Start panel pre-filled, and the sticky dock follows on mobile.
  - **A proof line and contents strip**: "planning items at 113 council and committee meetings across 69 of the 150
    councils we read" (computed from `data/excerpts/*/housing__*.json`), and the sample's sections with item counts as
    jump links.
  - A header with Energy / Housing edition switch and a "Start free" button. The uppercase kicker is gone.
- `radar tracker` now rebuilds housing.html on every deploy, so the counts stay current.
- **`site/start.js` (every page): the Start panel has an edition picker** (Energy projects / Land development &
  housing). Housing pages and any trial link whose subject says "Housing" open it in Housing. The trial email now says
  which edition ("...Council Radar, Land development & housing edition", subject ends "- Housing" or "- Energy").
  **Bug fixed:** before this, "skip the trial" in the panel on housing.html sent housing buyers to the *energy* Stripe
  links. In Housing it now uses the existing housing links with the existing `client_reference_id=housing` tag; energy
  behaviour and its `s_<councils>` tag are unchanged. Also fixed: panel text inputs overflowed the panel by a few pixels.
- New GA4 event `trial_request` (params: `edition`, `method` = mailto/gmail/outlook, `councils`) when someone presses a
  send button in the panel. `generate_lead` clicks are unchanged.

**Hypothesis.** Housing launched with a page that looked like a document, opened a trial panel that didn't mention
housing, and could charge housing buyers for the wrong product. A visitor who sees a real 987-unit proposal and their
own council's housing activity within one screen, and then a trial panel that names their edition, should request a
trial more often. The edition picker should also capture housing developers who land on the energy homepage.

**Files.** samples/build_housing_html.py, site/housing.html, site/start.js, radar/tracker.py, tests/test_radar.py.

**How to measure (GA4).**
- `generate_lead` events on page housing.html (method trial vs subscribe), week over week from Nov 24.
- New `trial_request` events, split by `edition`; watch for housing requests that start on index.html (picker working).
- Trial emails with subjects ending "- Housing"; Stripe sessions on the housing product (`client_reference_id=housing`).
- Engagement time on housing.html.

**Next to try.**
- Homepage: an edition choice above the fold (energy and housing developers both land there; housing is a footnote today).
- A housing share card (og image) with the notice sign, for LinkedIn posts aimed at planners and land-use lawyers.
- Per-council housing lines on council pages ("N meetings with housing items in the last 30 days").
- Link the OLT guide from housing.html, and the next housing guides (Bill 17/185, development charges, HAF) when written.
