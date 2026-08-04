# Changelog

All notable changes to PR HUB are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). Versions correspond to the
milestones in [`ROADMAP.md`](ROADMAP.md).

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
