# Roadmap

PR HUB is being built incrementally, one validated capability at a time.
Each version below has a single, testable objective — nothing ships until
the previous version's tests pass and, where applicable, its output has been
validated against real news.

---

## v0.7 — Deterministic Decision Engine & Validation Loop
**Status: ✅ Completed**

### Objective
Prove that a fully deterministic, YAML-configured Rule Engine can classify
real automotive PR news accurately enough to be useful, and build the
feedback loop needed to measure and improve that accuracy with evidence
instead of guesswork.

### Features
- Generic, domain-agnostic Rule Engine (`AND`/`OR`/`NOT` conditions,
  `single_winner` and `accumulate_all` resolution strategies)
- Knowledge Base: Brands, Competitors, Organizations (including the
  Stellantis corporate entity, added in this version), Products, Sources,
  Taxonomy, Event Types
- Entity Recognition (word-boundary-safe alias matching, disambiguation
  context) and Event Detection (keyword-based inference)
- Priority Rulebook v0.3 — 17 rules defined, 10 active
- Recommendation Engine with a 9-value closed action catalog
- Daily Brief Generator with an email-safe HTML renderer
- Training Mode: a real-news validation workflow producing a manual,
  human-readable report and an exportable JSON verdict record
- A full validation cycle executed once, end-to-end: 16 real news items
  classified → manually validated → root-caused
  (`validation_report.md`) → 4 fixes implemented → re-measured
  (`validation_delta.md`), moving estimated accuracy from 62.5% to ~75%
  on that sample
- 74 automated tests

### What's explicitly out of scope for v0.7
- No automated news ingestion — input is JSON, provided manually
- No email delivery — output is a local HTML file
- No sentiment/tone analysis — several rules are documented as blocked on
  this capability rather than implemented incorrectly
- No `Person` entity in the Knowledge Base
- No cross-story deduplication (`Story` vs. `NewsItem` distinction exists
  only in earlier architecture documents, not in this codebase yet)

---

## v0.8 — RSS Ingestion
**Status: 🔜 Planned**

### Objective
Replace manual JSON input with automated ingestion from real-time sources,
without changing anything downstream of ingestion.

### Planned features
- RSS connector(s) for the sources already cataloged in
  `config/knowledge_base/sources.yml`
- A scheduled ingestion run (cron-style), producing the same `NewsInput`
  shape the Rule Engine already consumes — **no changes to
  `rule_engine/`, `classification/`, or the Rulebook required**
- Basic cross-fetch deduplication (avoid re-processing the same article
  fetched twice), which is the first real step toward the `Story` vs.
  `NewsItem` distinction described in earlier architecture work but never
  implemented
- Source health monitoring (a feed that stops responding should be
  visible, not silent)

### Explicitly not in v0.8
- Email delivery (still v0.9)
- Sentiment analysis
- Multi-tenant / multi-client support

---

## v0.9 — Email Delivery
**Status: 🔜 Planned**

### Objective
Get the Daily Brief into the Coordinator's inbox automatically, every
morning, without anyone opening a terminal.

### Planned features
- Scheduled generation + delivery (Daily Brief and, if useful by then,
  Training Mode digests)
- Real Gmail/Outlook client rendering verification — `daily_brief.html`
  has only ever been verified in a headless browser and Chromium via
  Playwright; a real inbox test is a known open item
- A delivery failure channel independent of the Daily Brief channel
  itself (so a broken email integration doesn't fail silently)
- Delivery audit log (what was sent, when, to whom)

### Explicitly not in v0.9
- Two-way triage (replying to the email, marking things read) — Daily
  Brief remains a one-way push
- RSS ingestion improvements beyond what v0.8 shipped

---

## v1.0 — Production-Ready PR Intelligence Platform
**Status: 🔭 Vision — not yet scoped in detail**

### Objective
A fully operational, continuously self-improving tool the Coordinator
relies on daily, with the reliability and auditability the "PR HUB never
decides, it only assists" principle demands.

### Candidate features (subject to re-prioritization closer to the time)
- Sentiment/tone signal — this single capability unblocks multiple
  documented-but-pending rules (see `config/rules/*.yml` for the specific
  `todo` notes on each PENDING rule)
- `Person` entity in the Knowledge Base (spokesperson / Brand Manager /
  CEO detection)
- Persistent storage layer for audit trail and historical Story tracking
- A recurring Training Mode cadence (Round 2, 3, …) with a real
  measured accuracy trend, not a single estimated data point
- Expanded `RecommendationAction` vocabulary, informed by the open
  business conversation flagged in `validation_report.md` (item P7)
- Multi-client / multi-market configuration path, revisiting the
  isolation requirements noted in earlier architecture documents

### Explicitly out of scope, even for v1.0
- Any form of AI-driven classification of priority, category, or
  recommendation — that boundary is a design principle, not a temporary
  limitation, and isn't on this roadmap to be removed
