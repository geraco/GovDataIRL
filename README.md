# Ireland Open Data Analyst

Discovers a live API-backed dataset on data.gov.ie, profiles it deterministically,
runs a three-pass AI analyst pipeline over it, and publishes a static, fact-checked
report. Full design in [IRELAND_DATA_ANALYST_SPEC.md](IRELAND_DATA_ANALYST_SPEC.md).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in ANTHROPIC_API_KEY
```

## Run

```bash
python run.py               # refresh candidate pool, pick a dataset, publish
python run.py --no-refresh  # reuse the cached pool (faster, for iterating)
```

Output lands in `static_out/` — `index.html` is the archive, `reports/*.html`
are individual reports, `feed.json`/`feed.xml` are the archive feeds. Open
`static_out/index.html` directly in a browser; nothing needs to be served.

## What's stubbed

Netlify deploy and ntfy push (`publish/notify.py`) are no-ops until
`NETLIFY_SITE_ID`/`NETLIFY_AUTH_TOKEN` or `NTFY_TOPIC` are set in `.env`, per your
instruction to build the static-site pipeline first and wire up publishing later.

## Known gap — needs a live key to verify

The AI pipeline (`analyst/`) is built against the spec's Pass A/B/C contract
(structured tool-use output, JSON schemas matching §5.4/§12) but has **not been
run against a live Anthropic API key** — none was available in this session.
Every other stage (connectors, discovery/scoring, profiling, chart rendering,
report/site building, re-roll/skip hardening) has been smoke-tested against the
real data.gov.ie catalogue end-to-end, including a real failure/re-roll/skip
run (confirmed via the missing-key error). Run `python run.py` once
`ANTHROPIC_API_KEY` is set and check the output narrative reads sensibly before
trusting it unattended — the schema is right by inspection, but no live call
has confirmed Claude actually returns well-formed tool calls for all three
passes against a real profile.

## Candidate pool size

data.gov.ie currently tags only ~19 packages `res_format:API`; a handful more
surface via `datastore_active` resources that aren't labelled "API" (see
`discovery/probe.py`). This is a small pool for a "weighted random, exclude
last 30 days" scheme — expect the same handful of datasets to recur until the
catalogue grows or picks age out of the 30-day exclusion window.

## Repo structure

Matches spec §14 (`discovery/`, `connectors/`, `profiling/`, `analyst/`,
`rendering/`, `publish/`, `db/`, `config.py`, `run.py`).
