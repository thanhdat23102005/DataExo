# Research — the 50-site measurement study

This is the measurement study the rest of the project grew out of: an
automated crawl of 50 Australian websites across five sectors, recording
every outbound request and testing four stated hypotheses about it.

It is kept separate from `extension/` and `pi/` because it answers a
different kind of question. The extension and the Pi tell you what is
happening on your own network right now. This tells you what is true
across a sample of sites, with numbers that can be checked.

All commands below run **from this directory**.

## Setup

```bash
cd research
python -m venv .venv && ./.venv/bin/pip install -r ../requirements.txt
./.venv/bin/python setup_data.py --geoip-key YOUR_MAXMIND_KEY
```

To detect your own identifiers in the captured traffic, create
`data/identities.local.yaml` (gitignored, never committed):

```yaml
email:
  - your.real@email.com
phone:
  - "0412345678"
```

Without it the study still reports trackers, owners and countries; it just
cannot test the hash-matching hypothesis. Do not put a short placeholder
in there — a two-digit value matches almost every URL and floods the
results with noise.

## Run

```bash
python -m crawler.crawl --sector government   # one sector first, 10 sites
python -m crawler.crawl                        # all 50, ~20-30 min
python -m pipeline.process                     # classify + PII + risk → DuckDB
python -m analysis.report                      # H1-H4 tables and charts
python -m analysis.export_sheet                # per-site CSV + Excel with chart
python -m pytest tests/ -v
```

## Hypotheses

| | |
|---|---|
| **H1** | Tracker density differs by sector |
| **H2** | PII transmission rate differs by sector |
| **H3** | A majority of tracker destinations are offshore |
| **H4** | Mean risk score differs by sector |

## Classification is rule-based on purpose

Every label comes from EasyPrivacy and DuckDuckGo Tracker Radar, so any
result can be checked by hand against a public source. That is why the
sample stays at 50 sites: a number small enough to verify, rather than a
number large enough to sound impressive but impossible to audit.

`pipeline/ml_classifier.py` is a separate, exploratory question — can a
model learn to recognise a tracker from request shape alone, without a
blocklist? It is trained on the rule-based labels and does **not** feed
the study's numbers.

## Other pieces here

- `extension-agent/` — the earlier extension that pushes to
  `pipeline/agent.py` rather than to the Pi. Superseded by `extension/` at
  the top level; kept because the live-agent dashboard pairs with it.
- `monitoring/` — InfluxDB + Grafana, fed by `pipeline/agent.py`. Run
  `./monitoring/setup_monitoring.sh`; it downloads both and provisions the
  dashboard. Optional.
- `setup-rhel.sh` — system dependencies for Chromium on RHEL, which
  `playwright install-deps` does not handle there.

## Known issue

`tests/test_classify.py`, `tests/test_pii.py` and `tests/test_risk.py`
fail at import: they were written against an API (`registrable_domain`,
`IdentityIndex`, `level`) that does not exist in the current modules.
`tests/test_pipeline.py` and `tests/test_ml_classifier.py` pass. The
pipeline itself is unaffected — `process.py` and `agent.py` use the real
API — but the three stale files need rewriting or removing.
