# Changelog

All notable changes to PR HUB are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). Versions correspond to the
milestones in [`ROADMAP.md`](ROADMAP.md).

---

## [Unreleased] — v0.8-dev: RSS Ingestion (Sprint 9)

### Added
- `rss/` module: `feed_loader.py`, `fetcher.py` (HTTP + `file://`),
  `parser.py` (RSS 2.0 + Atom, stdlib-only, no new unverified
  dependencies), `normalizer.py`, `deduplication.py` (exact URL / exact
  normalized-title matching), `ingest.py` (orchestrator)
- `config/rss_sources.yml`: 11 feeds cataloged, each an honest record of
  whether its URL was actually confirmed (`verified: true/false`) rather
  than a uniform claim that all of them work
- `run_daily.py` is now the single daily command: RSS ingestion →
  `data/daily_input/YYYY-MM-DD.json` → the existing, unmodified pipeline
  → both `daily_brief.html` and `training_report.html`. The previous
  fictional-data behavior remains available via `--skip-ingestion`
- `examples/rss_demo/`: a runnable, network-free demonstration of the
  full ingestion path against local sample feeds (including one
  deliberately malformed, to show the graceful-failure path for real)
- 51 new automated tests: RSS/Atom parsing, deduplication, fetch
  failures (missing file, unsupported scheme, unreachable host),
  full-ingestion runs (partial failure, total failure, cross-feed
  deduplication, disabled feeds), and end-to-end integration proving the
  ingested JSON is consumable by the pipeline with zero changes to it

### Changed
- `run_daily.py`'s `process_daily_input()` now accepts either a directory
  of individual story files (original Sprint 4 behavior, unchanged) or a
  single JSON file containing a list of stories (new, what RSS ingestion
  produces) — same pipeline execution path either way, no duplicated logic

### Fixed (found while building this sprint, not pre-existing)
- Two bugs in this sprint's own test fixtures, not in production code:
  an unescaped `<link>` literal inside RSS `<description>` text that
  produced invalid XML, and a test assertion that incorrectly assumed
  CDATA content gets HTML-entity-decoded by the XML parser (it doesn't,
  by design — that's `rss/normalizer.py`'s job, confirmed by an added
  end-to-end test)

### Known limitations (see `ROADMAP.md`, v0.8, for the full list)
- Only 2 of 11 configured feed URLs were confirmed against a live
  connection (this development environment has an allowlisted egress
  proxy that didn't include the relevant hosts) — the rest need
  verification before production use
- `AutoTest` and `Motor1` feeds are blocked on a Knowledge Base addition,
  deliberately left out of scope for this sprint
- No scheduling (cron) yet — ingestion runs when `run_daily.py` is invoked
- Deduplication is exact-match only; no fuzzy/semantic matching

---

## [v0.7] — Deterministic Decision Engine & Validation Loop

The first version of PR HUB capable of taking a real news story and
producing a classification a PR Coordinator can act on — and the first
version with evidence, not just intuition, about how often it gets that
classification right.

### Added

**Core engine**
- Generic, domain-agnostic Rule Engine: `Fact` / `Rule` / `Outcome` model,
  `AND`/`OR`/`NOT` condition trees, `single_winner` and `accumulate_all`
  resolution strategies, full audit trail of every rule that matched (not
  only the winner)
- Knowledge Base Loader for Brands, Competitors, Organizations, Products
  (Models + Technologies), Sources, Taxonomy (Category/Subcategory), and
  Event Types
- Entity Recognition: deterministic alias matching with disambiguation
  context for ambiguous terms (e.g., "Jeep" as a brand vs. a generic
  Spanish word)
- Event Detection: keyword-based inference of `EventType` when not
  explicitly provided in the input
- A decoupled 5-stage pipeline (Entity Recognition → Event Detection →
  Priority Rule Engine → Recommendation Engine → Daily Brief Generator),
  each stage independently replaceable

**Rulebook**
- Priority Rulebook v0.3: 17 rules defined (10 active, 7 explicitly
  documented as pending on a named dependency — never silently missing)
- Recommendation Engine with a closed, 9-value action catalog

**Products**
- `main.py` — classify a single news item from the command line
- `run_daily.py` — batch-process a folder of news into `daily_brief.html`,
  an email-safe (Gmail/Outlook-oriented) executive HTML brief
- `run_training.py` + Training Mode — process real news, generate
  `training_report.html` for manual Sí/No validation per story, and export
  verdicts to JSON entirely client-side (no server, no network calls)

**Validation loop**
- 16 real news items (July/August 2026) covering Stellantis, competitors,
  and industry news, each with a verifiable source URL
- A complete first validation cycle: manual validation →
  `validation_report.md` (root-cause analysis, 62.5% baseline accuracy,
  8-item prioritized backlog) → 4 approved fixes implemented →
  `validation_delta.md` (re-measurement, ~75% estimated accuracy)

**Testing**
- 74 automated tests covering the Knowledge Base loader, Entity
  Recognition (including regression tests for two real bugs found via real
  news), Event Detection, the Rule Engine's condition/resolution logic, the
  decoupled pipeline, end-to-end story classification, Daily Brief
  aggregation, and the Training Mode report

### Fixed
- Entity Recognition matched substrings without word boundaries, causing a
  real false positive (`"ds"` inside `"Ads"`, from "premios Ads People
  Like", incorrectly detected the DS Automobiles brand). Fixed with
  word-boundary–aware matching; regression test added.
- `PR-013` (Latin NCAP safety results) did not distinguish a Stellantis
  brand from a competitor, producing the same `HIGH` priority and
  "prepare Q&A" recommendation for both — confirmed as a real
  misclassification in two separate real news items during validation.
  Split into `PR-013` (Stellantis brand → `HIGH`) and `PR-017`
  (competitor → `LOW`, competitive-intelligence framing).
- Stellantis (the corporate group) was undetectable as an entity — the
  Knowledge Base only modeled its 8 individual sub-brands. Added as a
  dedicated `Organization` entity, independent of `Brand` detection.
- Commercial/strategic alliance news mentioning Stellantis corporately
  (e.g., a financing partnership) had no matching rule and fell through
  unclassified. Added `PR-016`.

### Known limitations (by design, not oversight — see `ROADMAP.md`)
- No automated news ingestion (input is manual JSON)
- No email delivery (output is a local HTML file)
- No sentiment/tone signal — several rules are explicitly disabled pending
  this capability rather than approximated incorrectly
- No `Person` entity in the Knowledge Base
- `training_report.html` has been verified in a headless browser and in
  Chromium via Playwright, but not yet in a real Gmail/Outlook client
