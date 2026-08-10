# Ireland Open Data Analyst

Discovers a live API-backed dataset on data.gov.ie, profiles it deterministically,
detects real analytical insights, runs a two-pass AI narrative pipeline over it, and
publishes a static, fact-checked, editorially-charted report. Deploys automatically to
GitHub Pages: **https://geraco.github.io/GovDataIRL/**

Design docs: [IRELAND_DATA_ANALYST_SPEC.md](IRELAND_DATA_ANALYST_SPEC.md) (system
architecture) and [Data Visualisation and Graphical Storytelling
Specification.md](Data%20Visualisation%20and%20Graphical%20Storytelling%20Specification.md)
(presentation/analysis rules).

## Pipeline

```
discover (data.gov.ie) → connector → profile (deterministic stats)
  → insight engine (deterministic: biggest change, concentration, correlation, outliers)
  → Pass A (AI narrative, insight-led)  →  Pass C (AI fact-check vs. profile+insights)
  → chart selector (deterministic, binds real dataframe columns — no hallucinated fields)
  → Observable Plot charts → static HTML report → docs/ (GitHub Pages)
```

The chart-spec pass from the original spec (an AI proposing chart fields) was replaced
with `rendering/selector.py` — pure code that maps each insight category onto a chart
type and binds it directly to real dataframe columns. The AI's job is editorial
judgement (which insight is the story), never field-binding — that's what produced the
hallucinated-column bugs during development, and code doesn't have that failure mode.

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

Output lands in `docs/` — `index.html` is the archive, `reports/*.html` are individual
reports, `feed.json`/`feed.xml` are the archive feeds. `docs/` (not `static_out/`) is
the required folder name for GitHub Pages branch-deploy. Open `docs/index.html`
directly in a browser for local iteration; nothing needs to be served, except the
Observable Plot charts need network access to load `@observablehq/plot` from a CDN.

## Deployment

`.github/workflows/publish.yml` runs `run.py` daily at 06:00 UTC (and on manual
dispatch), commits `docs/` + `db/datagovie.sqlite` back to `main`, and GitHub Pages
branch-deploys from `main:/docs` automatically on push. `ANTHROPIC_API_KEY` is stored
as a repo secret. The SQLite DB is committed (not gitignored) specifically so run
history and the candidate pool persist across ephemeral CI checkouts — reports
themselves are also committed so the archive accumulates rather than resetting each run.

## What's stubbed

ntfy push (`publish/notify.py`) is a no-op until `NTFY_TOPIC` is set as a repo
secret/env var. Netlify was dropped entirely in favour of GitHub Pages.

## Candidate pool size

data.gov.ie currently tags only ~19 packages `res_format:API`; a handful more surface
via `datastore_active` resources that aren't labelled "API" (see `discovery/probe.py`).
This is a small pool for a "weighted random, exclude last 30 days" scheme — expect the
same handful of datasets to recur until the catalogue grows or picks age out of the
30-day exclusion window.

## Repo structure

```
discovery/    candidate pool, viability probe, interestingness scoring
connectors/   DataStore / PxStat / ArcGIS / generic-JSON, shape auto-detection
profiling/    deterministic stats (profiler.py) + insight detection (insights.py)
analyst/      Pass A (narrative) + Pass C (fact-check) — Anthropic structured tool-use
rendering/    chart selector (selector.py, deterministic) + Observable Plot renderer
publish/      Jinja2 site builder, ntfy notify stub
db/           SQLite: candidates, runs, reports
.github/workflows/publish.yml   daily discover→analyse→publish→commit→Pages
```
