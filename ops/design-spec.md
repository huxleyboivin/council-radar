# Council Radar: homepage design spec

The rules the homepage is built to. Change the page, then change this file. Last revised 2026-11-21.

## 1. What we took from leading B2B sites

| Site | What it does well | What we use |
|---|---|---|
| [Stripe](https://stripe.com) | One-line category claim, then proof at scale: big real numbers (uptime, reach) and a pricing section with no hidden fees. Reworks its homepage relentlessly. | A proof bar under the hero, made only of real counts from our own data. Plain pricing next to the by-hand calculator. |
| [Linear](https://linear.app) | Shows the actual product, not stock art: every section pairs a short claim with real UI. A changelog proves the product is alive. | The hero is a working tool (lookup, survey plan, card) and "How it works" shows the real Monday email. The live "Last read today at 6:44 a.m." line plays the changelog's role. |
| [FiscalNote](https://fiscalnote.com) (closest analog: policy tracking) | Coverage numbers ("12,000+ governments") and a closing line that splits the work: "We'll read the bills. You read the room." | The closing section states the same split for councils: we read the agendas, you make the call. |
| [Enverus](https://www.enverus.com/overview/) (energy data) | A stat grid of scale, plus photographs of the energy world beside product screens. | Real photographs of Ontario energy land and a council chamber, behind the product, never instead of it. |
| [Samsara](https://samsara.com) (physical operations) | Photography of the physical work the software serves, with product UI layered on top. | "The plan over the land": the survey-plan drawing sits on top of a real photo of a Wolfe Island farm with turbines. |

What we deliberately don't copy:
- **Logo walls and testimonials.** We have no customers yet, and inventing them is not an option. Proof comes from coverage, freshness and sources instead.
- **Animated gradients.** They're Stripe's signature, not ours.

## 2. Layout structure (homepage, top to bottom)

```
┌───────────────────────── header (logo · nav · Free trial) ─────────────────────────┐
│ HERO STAGE  full-bleed photo: Wolfe Island farm, bales, rail fence, turbines       │
│  ┌ paper wash, left → right ┐                                                      │
│  │ live line                 │                    ┌──────────────────────────┐     │
│  │ H1 (3 lines)              │                    │ survey plan (sheet)      │     │
│  │ subhead                   │                    │ parcels = decisions      │     │
│  │ [ lookup ............ ]   │                    └──────────────────────────┘     │
│  │ try chips / watchlist     │                    [ council card when chosen ]     │
│  │ [Subscribe] [Free issue]  │                                                     │
└──┴───────────────────────────┴─────────────────────────────────────────────────────┘
  WINDOW 2   clock band on paper
  CALENDAR   ink band over a full-bleed photo of an empty council chamber: free feeds + "this week" calendar
  WHY / WHO / HOW IT WORKS (steps + the real Monday email) / TRACKER
  PRICING    by-hand calculator, then the plans
  FAQ
  CLOSING    "We read the agendas. You make the call." + CTAs
  FOOTER     address, analytics note, guides, photo credits
```

- **Alignment:** left-aligned text everywhere. Centred text appears only inside buttons.
- **Content width:** 72rem with 1.5rem gutters. Body text stays under 44rem (about 75 characters).
- **One job per section.** A section that needs two calls to action is two sections.

## 3. Visual constraints

**Colour.** Ink `#14284B`, paper `#FFFFFF`, mist `#EEF3F8`, line `#D5DCE5`. Decision colours carry meaning and are used for nothing else:
- support given `#2E7D4F`
- no support `#B3412E`
- new rules `#2F6FB5`
- early signal `#A86F0E`
- subscriber item `#6A5BB5`

**Type.**
- Barlow Semi Condensed for headings.
- Barlow Condensed inside the survey plan only.
- Public Sans for everything else.
- Sentence case throughout. Capitals appear only where the subject's own vernacular demands it (road names and the title block on the plan).

**Photography.**
- Real, freely licensed photographs of Ontario energy land and council rooms only. No stock people, no illustrations pretending to be photos, no AI-generated images.
- Every photo is credited in the footer, with author and licence.
- Photos always sit under a wash: paper (white) on the hero, ink on the chamber band. Text never sits on raw photo pixels.
- A page without its photos must still look finished, so each stage has a solid background colour as a fallback.

**Anti-cliché rules (checked on every change):**
- No capitalized labels above headings, and no words in a heading styled differently from the rest.
- No numbered circles unless the content is a real sequence ("How it works" is one).
- No "→" glued onto buttons or links.
- No identical card grids with the same shadow; the survey plan, the email and the clock each have their own form.
- No gradient blobs, glassmorphism or decorative 3D.
- No invented numbers, logos or quotes. Every figure on the page is computed from `councils.json` or quoted with a source.

**Contrast.** Body text ≥ 4.5:1 and large text ≥ 3:1, measured against the *washed* photo at its brightest point.

## 4. Interaction mechanics

| Element | Trigger | What happens | Timing |
|---|---|---|---|
| Page load | first paint | Hero photo settles (opacity 0→1, scale 1.03→1); radar sweep crosses the plan and lights each parcel by bearing | photo 900 ms; sweep 2.4 s, starts at 0.3 s |
| Lookup | type 1+ characters | Dropdown fades and slides 4 px into place; arrow keys move, Enter picks, Esc closes | 160 ms |
| Pick a council | Enter, click or "Try" chip | Card cross-fades in (view transition where supported); the plan highlights its parcel, or stakes out an empty lot | 280 ms |
| Switch council | pick another | The old card cross-fades out as the new one comes in, with no jump | 280 ms |
| Add to my councils | button | Button turns to "Added"; a chip pops into the watchlist; the dock appears once the watchlist is off screen | chip 200 ms, dock 320 ms |
| Start panel | any trial link or the dock | Slides in from the right with the backdrop fading in; closing reverses (it no longer vanishes) | 280 ms in, 200 ms out |
| Calculator | slider or scope | Bars resize with transform (scaleX), not width | 350 ms |
| Page to page | any same-site link | Cross-document view transition: a short cross-fade | 200 ms |

**Motion tokens:**
- easing `--ease-out: cubic-bezier(.2,.8,.2,1)` and `--ease-in-out: cubic-bezier(.65,0,.35,1)`
- durations 140 ms (hover), 200 ms (small open/close), 280 ms (panels, cards), 420 ms and up (staged moments)

**Motion rules:**
- Animate only `transform` and `opacity`.
- No scroll-triggered fade-ins: sections are simply there.
- One orchestrated moment per page (the load sequence).
- `prefers-reduced-motion: reduce` removes every non-essential animation, the photo settle and view transitions included.

## 5. Responsive behaviour

| Width | Changes |
|---|---|
| ≥ 1200 px | Two-column hero; plan at 32rem; the plan sheet covers the near turbine until a council card opens, and the horizon turbines show to its right |
| 900–1199 px | Same layout with narrower gaps; headline still 3–4 lines |
| 700–899 px | Hero stacks: text, then plan, then card. The photo runs from the top to halfway down the plan under a top-to-bottom paper wash, so the near turbine shows behind the headline. Clock becomes a list. Calendar band stacks. |
| < 700 px | Body 17 px; buttons full width; dock becomes a bottom bar; the Start panel takes the full screen; the chamber photo is cropped to the desks (`object-position: 50% 55%`) |
| < 400 px | Plan text stays ≥ 9 px effective; "Try" chips wrap; no horizontal scroll at 320 px |

- **Images** load from Wikimedia at standard widths (960/1280/1920) through `srcset`/`sizes`. The hero photo loads eagerly with `fetchpriority="high"`; the chamber photo loads lazily.
- **Keyboard:** everything is reachable by keyboard, with a visible focus ring (3 px, `#2F6FB5`).

## 6. As built (Nov 21) and why it differs

- **No proof bar.** The live line above the headline already states the real counts ("Last read today at 6:44 a.m.: 1,622 documents from 150 councils"). A second row of the same numbers would only repeat it, in the big-number layout every SaaS page uses.
- **The chamber photo went on the calendar band, not the Window 2 band.** The calendar band is about meetings, which is what the chamber shows, and it was already ink. An ink Window 2 band right above it would have merged the two into one dark block.
- **Contrast is measured, not guessed.** The worst single background pixel under each text block, with the hero's secondary text at `#43506A`, gives: subhead 5.6:1, chips 6.4:1, "Read a sample issue" line 5.3:1 (390 px), and calendar band body 5.1:1. Re-run `contrast_test.py` after changing a photo or a wash.
