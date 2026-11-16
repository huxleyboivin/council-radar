# Council Radar

AI-read Ontario council agendas, sold as narrow weekly alert feeds. Feed #1:
**Ontario Energy Projects**: every council move on IESO municipal support
confirmations, energy-siting protocols, zoning and delegations.

## How it runs (no human in the loop)

| When | Workflow | What happens |
|---|---|---|
| Daily ~5:23 a.m. ET | `daily.yml` | Pull new meetings/documents from every monitored eScribe portal, keyword-prefilter, AI-read matches, store findings in `data/radar.db`, write `data/health.json` |
| Mondays ~6:41 a.m. ET | `weekly.yml` | Render the issue per feed, deliver via Buttondown (draft or send) |
| Monthly | `discover.yml` | Probe all Ontario municipalities for eScribe portals; add finds to `data/discovered.yaml` |
| Every push | `tests.yml` | Unit tests |

A weekly Claude scheduled task acts as maintainer: reads `health.json` and
`last_run_errors.json`, fixes broken parsers, spot-checks findings against sources,
and emails the owner a short report.

## Secrets / variables (repo Settings → Secrets and variables → Actions)

- `ANTHROPIC_API_KEY` (secret): AI reading. Set a monthly spend limit in the Anthropic console.
- `BUTTONDOWN_API_KEY` (secret): delivery. Buttondown handles Stripe billing and unsubscribes.
- `RADAR_DELIVERY_MODE` (variable): `draft` (default) or `send`.

## Local use

```bash
pip install -r requirements.txt pytest
python -m pytest -q
python -m radar run --only ottawa     # needs network access to the portal
python -m radar digest                # writes data/issues/<date>-<feed>.md
```

## Adding a feed

Add a block to `feeds.yaml` (patterns + categories). The same collected documents
are read for every enabled feed; only matching passages are sent to the model.

## Ground rules

Public records only. Requests identify the bot, honour robots.txt and are spaced
out. Every finding links to its source document; issues carry an accuracy disclaimer.
