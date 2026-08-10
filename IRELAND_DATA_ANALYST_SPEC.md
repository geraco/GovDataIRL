# Ireland Open Data Analyst — Technical & Design Specification

**Working name:** `datagovie-analyst` (placeholder — bikeshed later)
**Author:** Spec drafted for Gerry, for handoff to Claude Code
**Status:** v1 draft, pre-build
**Purpose:** An autonomous tool that discovers a public API-backed dataset on data.gov.ie, runs an AI-driven analytical pass over it, and publishes a public-facing, editorially written insight report — repeatable on a schedule, browsable as an archive.

---

## 1. Concept Summary

A background job selects one live, queryable dataset from data.gov.ie's catalogue of API-backed resources, profiles it statistically, hands that profile (not the raw firehose of data) to an AI "analyst" persona, verifies the analyst's claims against the actual computed numbers, generates real charts from real data, and publishes the result as a short, readable report aimed at an intelligent lay reader — not a BI dashboard aimed at an analyst.

The interesting engineering problem isn't "call an API and summarise it" — it's that data.gov.ie's "API" resources are not one API. They're five or six different API shapes wearing the same label. The system has to detect what it's actually looking at, extract data from it safely, and fail gracefully (re-roll) when a resource is unusable, dead, or too geospatial/binary to narrate sensibly.

---

## 2. Objectives & Success Criteria

| Objective | Success looks like |
|---|---|
| Discover viable datasets automatically | Nightly job builds a scored pool of "narratable" resources without manual curation |
| Produce genuinely interesting output | Report contains at least one non-obvious, numerically grounded finding — not just "here is the average" |
| Be trustworthy | Every quantitative claim in the narrative is checked against a computed value before publishing; no claim ships unverified |
| Be public-facing quality | Reads like a short data-journalism piece (FT/Our World in Data register), not a JSON dump with prose glued on |
| Be low-maintenance | Runs unattended; broken/dead APIs are skipped and logged, not fatal |
| Build a growing asset | Each run adds to a browsable public archive, not a single ephemeral page |

Non-goals for v1: user accounts, dataset submission by the public, real-time streaming data, datasets requiring auth/API keys beyond data.gov.ie's own (which is keyless).

---

## 3. Data Source Analysis — What's actually behind the URL

`https://data.gov.ie/dataset/?api=true` is the CKAN 2.9 dataset-search UI with a resource-format facet applied. The real integration surface is the CKAN Action API:

```
GET https://data.gov.ie/api/3/action/package_search?fq=res_format:API&rows=100
GET https://data.gov.ie/api/3/action/package_show?id={dataset-slug}
GET https://data.gov.ie/api/3/action/resource_search?query=format:API
GET https://data.gov.ie/api/3/action/datastore_search?resource_id={id}&limit=100
```

No API key is required for read access. Rate limiting is not formally published — the connector layer should self-throttle (see §6.2) and cache aggressively regardless.

### 3.2 The resource-shape problem

Filtering `res_format:API` returns resources tagged "API" but the underlying shape varies:

1. **CKAN DataStore** — resource has `datastore_active: true`; queryable via `datastore_search` with real filtering/paging. Best case: structured, typed, paginated JSON.
2. **CSO PxStat / StatBank endpoints** — Central Statistics Office data (a large fraction of the interesting demographic/social datasets — the GUI cohort study, homelessness stats, disability/health survey data all sit here). These use the PxStat/PX-Web JSON-stat convention, not plain tabular JSON. Needs its own parser (JSON-stat → dataframe).
3. **ArcGIS FeatureServer / MapServer** — spatial data (planning applications, zoned land prices, valuation data). Returns GeoJSON-ish structures via `/query?f=json`. Numeric/categorical fields inside `attributes` are narratable; geometry itself generally isn't for this tool's purpose.
4. **OGC WFS/WMS** — older geospatial standard, XML-flavoured. Lower priority to support in v1; detect and skip gracefully.
5. **Bespoke REST APIs** — individual public bodies (Valuation Office, local authorities) running their own lightly-documented JSON APIs. Treat as "unknown JSON" — attempt generic ingestion, fall back to skip if structure can't be flattened.

**Design consequence:** the connector layer is a strategy pattern, not a single HTTP client. See §6.

### 3.3 Narratability filter

Not every valid dataset makes an interesting report. A geometry-only spatial layer or a single-row lookup table is technically fetchable but has nothing to say. The discovery stage scores candidates and only pools the ones above a threshold (§6.1).

---

## 4. System Architecture

```
                    ┌─────────────────────────────────────────┐
                    │            SCHEDULER (cron)              │
                    │   nightly discovery + on-demand trigger  │
                    └───────────────────┬───────────────────────┘
                                        │
                 ┌──────────────────────▼──────────────────────┐
                 │   1. DISCOVERY ENGINE                        │
                 │   package_search → candidate pool             │
                 │   → viability probe → interestingness score   │
                 │   → weighted-random pick (excl. recent picks) │
                 └──────────────────────┬──────────────────────┘
                                        │  chosen resource_id
                 ┌──────────────────────▼──────────────────────┐
                 │   2. UNIVERSAL CONNECTOR LAYER                │
                 │   detects shape → DataStore | PxStat |         │
                 │   ArcGIS | WFS | Generic JSON                 │
                 │   → normalised DataFrame                       │
                 └──────────────────────┬──────────────────────┘
                                        │  clean dataframe + metadata
                 ┌──────────────────────▼──────────────────────┐
                 │   3. PROFILING ENGINE (deterministic)         │
                 │   pandas: dtypes, nulls, cardinality,          │
                 │   distributions, time-series detection,        │
                 │   correlations, outliers                       │
                 └──────────────────────┬──────────────────────┘
                                        │  structured profile (JSON)
                 ┌──────────────────────▼──────────────────────┐
                 │   4. AI ANALYST PIPELINE (Claude Sonnet)      │
                 │   Pass A — Hypothesis & narrative draft        │
                 │   Pass B — Chart spec selection (grounded)     │
                 │   Pass C — Fact-verification against profile   │
                 └──────────────────────┬──────────────────────┘
                                        │  verified narrative + chart specs
                 ┌──────────────────────▼──────────────────────┐
                 │   5. CHART RENDERER (Plotly, from real data)   │
                 └──────────────────────┬──────────────────────┘
                                        │
                 ┌──────────────────────▼──────────────────────┐
                 │   6. REPORT BUILDER → static HTML page         │
                 │   + archive index update + RSS/JSON feed        │
                 └──────────────────────┬──────────────────────┘
                                        │
                 ┌──────────────────────▼──────────────────────┐
                 │   7. PUBLISH (Netlify) + ntfy notification      │
                 └───────────────────────────────────────────────┘

SQLite runs alongside every stage: candidate pool, pick history, run log, verified reports.
```

---

## 5. Component Design

### 5.1 Discovery Engine

- Pulls the full `res_format:API` candidate set weekly (cheap, cached to SQLite), refreshes viability status nightly on a rolling subset (not all — respect rate limits).
- **Viability probe:** lightweight HEAD/small-sample GET per candidate resource; records: reachable (bool), shape (enum), row-count estimate, column count, has-numeric-field (bool), has-time-field (bool), has-categorical-field (bool).
- **Interestingness score** (0–100), simple weighted heuristic, tunable:
  - +30 has a genuine time dimension (enables trend narrative)
  - +20 has ≥2 numeric fields (enables correlation/comparison narrative)
  - +15 has a meaningful categorical breakdown (enables "X vs Y" narrative)
  - +15 row count in a sweet spot (50–500,000 — enough to be real, not so much it's unwieldy)
  - −25 geometry-only / no non-spatial attributes
  - −20 single-row or near-static lookup table
  - −40 unreachable / malformed response
- Pool = candidates scoring ≥ 50. Selection = weighted random from the pool, excluding anything picked in the last N days (configurable, default 30) to force variety across the archive.
- On total connector failure for the chosen pick (dead mid-run), engine re-rolls once automatically, then logs and skips the run rather than publishing a broken report.

### 5.2 Universal Connector Layer

Strategy interface: `fetch(resource_metadata) -> pandas.DataFrame, source_notes`

- `DataStoreConnector` — `datastore_search` with paging, `q`/`filters` unused in v1 (full pull up to a sane row cap, default 20,000 rows, sampled if larger).
- `PxStatConnector` — fetches JSON-stat payload, unpivots dimensions into a tidy long-format dataframe (this is CSO's format — worth getting right, since it unlocks the richest social/demographic datasets).
- `ArcGISConnector` — queries `/query?where=1=1&outFields=*&f=json`, flattens `attributes`, drops raw `geometry` from the analytical dataframe but retains centroid/count-by-area if easily derivable.
- `GenericJSONConnector` — fetches, attempts `pandas.json_normalize` on the most plausible top-level list key; if it can't produce a rectangular structure with ≥2 usable columns, raises `NotNarrable` and the run re-rolls.
- All connectors return a common `source_notes` block: original URL, licence string (from CKAN package metadata — important, always carry and display this), last-updated date from the dataset's CKAN metadata, and the publishing body.

### 5.3 Profiling Engine (deterministic, no AI)

This stage exists specifically so the AI never has to "eyeball" raw data and never invents a statistic. Computes and hands forward as structured JSON:

- Per-column: dtype, null %, cardinality, min/max/mean/median/stddev (numeric), top-N value counts (categorical), detected date range (temporal)
- Correlation matrix for numeric column pairs above a threshold
- Simple outlier flags (IQR-based)
- Time-series resample (if a time column exists) at sensible granularity, with period-over-period % change
- A capped **data sample** (e.g. 20 representative rows, not the full set) — included so the model has concrete texture to write from, but this is clearly labelled "sample, not full population" in the prompt so it isn't mistaken for the whole picture

### 5.4 AI Analyst Pipeline (three Claude passes, deliberately separated)

**Why three passes and not one:** a single "here's the data, write me something interesting" prompt is exactly how you get confident, plausible-sounding, wrong numbers in a public-facing report. Separating draft → chart-grounding → fact-check catches that before publish.

**Pass A — Analyst draft.** System prompt establishes a senior public-sector data analyst persona (see §12 for the actual prompt). Input: the profiling JSON + capped sample + dataset metadata (title, publisher, licence, description from CKAN). Output: a structured narrative — headline finding, 3–5 supporting observations, one caveat/limitation paragraph (every report must name at least one), written for a general audience.

**Pass B — Chart specification.** Given the same profile, the model proposes 2–3 chart specs as structured data (chart type, x/y fields, aggregation, title) — not the chart itself. This spec is then executed against the *real* dataframe by the renderer (§5.5), so the chart is guaranteed to reflect actual computed values, never a hallucinated shape.

**Pass C — Fact verification.** A second, separately-invoked model call is given the Pass A narrative *and* the raw profiling JSON, and asked only to check: does every number, trend direction, and superlative claim in this text match a value actually present in the profile? Flags any unsupported claim. Unsupported claims are either auto-corrected against the true value or stripped — the run does not publish with an open flag.

### 5.5 Chart Renderer

Plotly (Python), executed against the actual dataframe using Pass B's spec. Output as static SVG embedded in the report (no client-side data dependency, keeps pages fast and archivable) — see §9 for why static over interactive by default.

### 5.6 Report Builder

Renders a Jinja2 template into a single static HTML file per report, plus updates a JSON index and an RSS feed for the archive. No server-side rendering at request time — everything is pre-built, matching your existing Financial Analyst / Christchurch pattern of static-first, dumb-hosting-friendly output.

### 5.7 Publishing & Notification

Netlify deploy (consistent with your existing dashboard pattern). Optional `ntfy` push on publish, matching your Financial Analyst alerting habit — "New data story: [headline]" with a link.

### 5.8 Archive

Every report is permanent, addressable by slug + date. Index page lists reports reverse-chronologically with a one-line teaser (Pass A's headline). This is the compounding asset — six months in, it's a small public data-journalism back-catalogue, which is a much stronger "interesting" outcome than any single report.

---

## 6. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.13 | Matches your existing stack (Financial Analyst, Teacher Planner) |
| Scheduling | OS cron (or APScheduler if you want it self-contained) | No need for a heavier orchestrator at this scale |
| HTTP | `httpx` | Async-capable, better timeout/retry ergonomics than `requests` |
| Data handling | `pandas` | Standard, matches Financial Analyst |
| AI | Anthropic SDK, Claude Sonnet for all three passes | Sonnet is the right cost/quality point for narrative + verification; no need for Opus here given the deterministic profiling does the heavy numeric lifting |
| Charts | `plotly` → static SVG export via `kaleido` | Consistent visual language, no JS chart runtime dependency in the published page |
| Templates | `Jinja2` | Static HTML generation |
| Storage | SQLite | Candidate pool, pick history, run log, published report metadata — consistent with your other local-first tools |
| Frontend | Hand-written HTML/CSS + minimal vanilla JS | Matches Christchurch pub site approach; no framework needed for a static, mostly-read-only public site |
| Hosting | Netlify | Matches Financial Analyst dashboard pattern |
| Notifications | ntfy | Matches your existing alerting habit |
| Geospatial handling | `shapely` (optional, only if ArcGIS centroid/area work is worth it) | Keep as a stretch item, not core path |

Deliberately excluded: FastAPI/React (no interactive backend needed — this is a batch job that publishes static output, not a live app), any database beyond SQLite (no concurrency requirement), any auth layer (public tool, public data).

---

## 7. Design Guide — Visual Identity

Target register: **editorial data journalism**, not corporate BI dashboard. Closest reference points: Our World in Data, FT Visual & Data Journalism, The Pudding — clean, chart-forward, generous whitespace, one confident accent colour, restrained chrome.

### 7.1 Typography
- **Headline/display:** a serif with character for headlines and pull-quotes (e.g. `Source Serif 4` or `Lora`) — signals "this was written," not "this was generated by a dashboard."
- **Body/UI:** a clean grotesk (e.g. `Inter` or `IBM Plex Sans`) for body text, captions, chart labels, metadata.
- **Numerals:** tabular figures for any inline stats so numbers align cleanly.

### 7.2 Colour
- Neutral base: near-white background (`#FAFAF7`, warm off-white rather than clinical pure white), near-black text (`#1A1A18`).
- **One accent colour**, used sparingly and consistently across the whole archive (not re-randomised per report) — e.g. a confident teal or burnt orange — used for: the single most important number/finding highlighted in each report, chart primary series, link states.
- Charts use a small, fixed categorical palette (3–5 colours max) derived from the accent, not default Plotly colours.
- Muted grey for source/licence/metadata footer text — present but visually secondary.

### 7.3 Layout
- Single-column reading width (~680px) for the narrative, matching a well-set article, not a dashboard grid.
- Charts break slightly wider than the text column for visual weight at their moment, then return to column width.
- Each report opens with: dataset title (plain language, not the raw CKAN slug), one-line "what this data is," publisher + licence badge, last-updated date.
- Closes with: explicit caveat/limitations paragraph (always present — this is a trust signal, not boilerplate) and a "Source & method" collapsible section — link to the raw dataset on data.gov.ie, the exact API endpoint used, and a one-line note on how the interestingness score picked it (transparency about the selection mechanism itself is part of the credibility story).

### 7.4 Archive/index page
- Simple reverse-chronological list, each entry: headline, one-line teaser (Pass A's finding, not a generic description), publisher tag, date. No thumbnails needed — text-forward, fast-loading.

### 7.5 Tone of voice (for the AI analyst prompt, §12)
Confident but hedged where the data warrants it; plain language over jargon; leads with the finding, not the methodology; treats the reader as smart but not a statistician.

---

## 8. Data Model (SQLite)

```sql
-- discovered candidates, refreshed on a rolling basis
candidates (
  resource_id TEXT PRIMARY KEY,
  package_id TEXT,
  title TEXT,
  publisher TEXT,
  licence TEXT,
  shape TEXT,              -- datastore | pxstat | arcgis | wfs | generic_json | unreachable
  last_probed_at TIMESTAMP,
  reachable BOOLEAN,
  row_estimate INTEGER,
  has_numeric BOOLEAN,
  has_temporal BOOLEAN,
  has_categorical BOOLEAN,
  interestingness_score INTEGER
);

-- every run, whether published or skipped
runs (
  run_id TEXT PRIMARY KEY,
  resource_id TEXT,
  started_at TIMESTAMP,
  status TEXT,              -- success | reroll | skipped | failed
  failure_reason TEXT,
  published_report_id TEXT
);

-- published reports = the public archive
reports (
  report_id TEXT PRIMARY KEY,
  resource_id TEXT,
  slug TEXT UNIQUE,
  headline TEXT,
  published_at TIMESTAMP,
  narrative_json TEXT,      -- full Pass A/B/C output, for audit
  html_path TEXT
);
```

---

## 9. Frontend Solution — Detail

Static-first is a deliberate choice, not a shortcut: the report content is generated once and doesn't need to react to anything at read time, so there is no benefit to shipping a JS framework, and a real cost (slower loads, dependency surface, harder to archive/re-host later). Charts are pre-rendered SVG rather than client-side Plotly.js — the reader gets the chart instantly, and the page has zero runtime dependency on a charting library actually loading correctly on someone's phone on 4G at an airport gate.

Minimal vanilla JS is still fine for: archive page filter/search-by-publisher, a "surprise me" button that jumps to a random past report, and a lightweight expand/collapse for the "Source & method" section.

If, later, a specific report genuinely benefits from an interactive element (e.g. a filterable time series), that can be a per-report opt-in Plotly.js embed rather than a site-wide default — keep the baseline fast and simple.

---

## 10. Error Handling & Resilience

- Connector failure → one automatic re-roll from the candidate pool → if that also fails, log and skip the run entirely (no partial/broken report ever ships).
- Fact-verification failure on a claim → auto-correct against true value where trivial (e.g. wrong % quoted), else strip the sentence — never publish an unverified quantitative claim.
- Rate-limit self-throttling on the CKAN API: fixed delay between requests during discovery probing (candidate pool building doesn't need to be fast), cached probe results reused across runs rather than re-probed every night.
- Dead/moved resources (CKAN packages do get archived) are marked `reachable = false` and drop out of the pool automatically on next probe cycle — no manual pruning needed.

---

## 11. Build Phases

1. **Phase 1 — Connector proof of concept.** Build the four connector strategies against real resource IDs pulled from `package_search?fq=res_format:API`. Confirm each shape can produce a clean dataframe. This is the highest-risk, highest-uncertainty part — do it first.
2. **Phase 2 — Discovery & scoring.** Candidate pool builder, viability probe, interestingness scoring, weighted random pick with recency exclusion.
3. **Phase 3 — Profiling engine.** Deterministic stats module, fully independent of AI — testable on its own with fixed sample datasets.
4. **Phase 4 — AI analyst pipeline.** Three-pass Claude integration, starting with Pass A alone against a fixed known-good dataset, then adding B and C.
5. **Phase 5 — Report builder & design.** Jinja2 templates, CSS, chart rendering, archive index.
6. **Phase 6 — Publish & schedule.** Netlify deploy pipeline, cron job, ntfy notification.
7. **Phase 7 — Hardening.** Re-roll logic, failure logging, a small backlog of manually-reviewed early reports before it runs fully unattended.

---

## 12. AI Analyst System Prompt — Working Draft (Pass A)

```
You are a senior public-sector data analyst writing a short public-facing
briefing about an Irish government open dataset. Your reader is intelligent
and curious but not a statistician.

You will be given:
- Dataset metadata (title, publisher, licence, last updated)
- A deterministic statistical profile of the dataset (computed in code —
  treat every number in this profile as ground truth)
- A capped sample of rows (illustrative only — NOT the full dataset;
  never treat the sample as complete)

Write:
1. A one-sentence headline finding
2. 3-5 supporting observations, each grounded in a specific number from
   the profile
3. One explicit caveat or limitation of this data (always required —
   e.g. sample size, missingness, self-reported nature, date range,
   geographic coverage gaps)

Rules:
- Every number you state must come from the profile, not be estimated
  or invented
- Do not extrapolate beyond what the data supports
- Plain language over statistical jargon
- If the data is genuinely uninteresting, say so plainly rather than
  manufacturing a finding
```

(Pass C's verification prompt is structurally similar but takes the Pass A output plus the profile and returns a pass/fail + corrections list per claim — build this as a strict JSON-output prompt so it's programmatically checkable.)

---

## 13. Open Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Hallucinated statistics in a public-facing report | Three-pass pipeline with dedicated fact-verification pass; no unverified claim ships (§5.4, §10) |
| CSO/PxStat data misinterpreted (these datasets often carry methodological caveats — survey weighting, small sample flags) | Carry forward any CKAN dataset notes/description into the prompt context; caveat paragraph is mandatory, not optional |
| Selection bias — tool always picks "safe," boring, well-structured datasets | Interestingness scoring should be tuned/reviewed periodically, not treated as fixed; consider logging *rejected* high-score candidates for occasional manual review |
| Dead/moved CKAN resources over time | Automated reachability re-probing drops them from the pool without manual intervention (§10) |
| Rate limiting or informal throttling from data.gov.ie | Self-imposed delays + heavy caching of discovery probes (§10) |
| Sensitive data inadvertently surfaced (some CSO datasets touch health/disability/homelessness — aggregate, not individual, but framing matters) | Analyst prompt explicitly instructed toward population-level, non-stigmatising framing; consider a manual review gate specifically for datasets tagged under sensitive categories before first automated publish of that category |

---

## 14. Suggested Repo Structure

```
datagovie-analyst/
├── discovery/
│   ├── probe.py
│   └── scoring.py
├── connectors/
│   ├── base.py
│   ├── datastore.py
│   ├── pxstat.py
│   ├── arcgis.py
│   └── generic_json.py
├── profiling/
│   └── profiler.py
├── analyst/
│   ├── pass_a_draft.py
│   ├── pass_b_charts.py
│   └── pass_c_verify.py
├── rendering/
│   ├── charts.py
│   └── templates/
├── publish/
│   └── build_site.py
├── db/
│   └── schema.sql
├── config.py
└── run.py          # entry point: discover → analyse → publish
```

---

*This spec is written for handoff to Claude Code. Phase 1 (connector proof of concept against real resource IDs) is the recommended starting point, since it's where the real uncertainty in this build lives — everything downstream assumes clean dataframes are achievable across all four connector shapes.*
