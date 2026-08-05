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
**Status: 🚧 In Progress — core ingestion built and tested (Sprint 9), feed verification and scheduling still open**

### Objective
Replace manual JSON input with automated ingestion from real-time sources,
without changing anything downstream of ingestion.

### Delivered in Sprint 9
- `rss/` module: fetch (HTTP + `file://` for local testing), parse (RSS 2.0
  and Atom, stdlib-only), normalize, and deterministic deduplication
  (same URL or same normalized title)
- `config/rss_sources.yml`: 11 feeds cataloged, each referencing a
  `source_id` that already exists in `config/knowledge_base/sources.yml` —
  no Knowledge Base changes were made to support ingestion
- `python run_daily.py` is now the single command: RSS → 
  `data/daily_input/YYYY-MM-DD.json` → existing pipeline (unchanged) →
  `daily_brief.html` + `training_report.html`
- Per-feed resilience: one broken feed doesn't stop the rest — verified
  against real (allowlist-blocked) network calls during development, not
  only mocked failures
- 51 new automated tests (parsing, deduplication, fetch failures, full
  ingestion runs, end-to-end integration with the unmodified existing
  pipeline)

### Explicitly still open (not silently missing)
- **Feed verification**: only 2 of 11 feed URLs (Diario Financiero,
  BioBioChile) were confirmed against a live connection — the rest are
  best-effort and need checking against real network access before
  production use (see `verified: false` entries in `rss_sources.yml`)
- **`AutoTest` and `Motor1`** feeds are blocked on a Knowledge Base change
  (their `source_id` doesn't exist yet in `sources.yml`) — deliberately
  out of scope for an ingestion-only sprint
- **Scheduled/cron execution** — today, ingestion runs when `run_daily.py`
  is invoked, not on a timer
- **Source health monitoring** — a feed that starts failing is logged per
  run, but there's no persisted history of feed reliability over time yet
- **Fuzzy/semantic deduplication** — only exact URL and normalized-title
  matches are caught; two articles covering the same event with
  differently-worded headlines are still treated as separate stories

### Explicitly not in v0.8
- Email delivery (still v0.9)
- Sentiment analysis
- Multi-tenant / multi-client support

---

## v0.9 — Email Delivery
**Status: 🚧 In Progress — SMTP sending built and tested, scheduling and real-inbox verification still open**

### Objective
Get the Daily Brief into the Coordinator's inbox automatically, every
morning, without anyone opening a terminal.

### Delivered
- `email_delivery/` module: builds a `multipart/alternative` MIME message
  (HTML + plain-text fallback) from the already-generated
  `daily_brief.html`, and sends it via `smtplib` (STARTTLS supported)
- `config/email_config.yaml` — no credentials committed, ever; username
  and password are read from environment variables at send time, or the
  send fails loudly with `MissingCredentialError`
- `run_daily.py --send-email`, fully opt-in — verified via a real CLI
  subprocess run, both with and without the flag, to confirm the default
  flow is untouched
- The real SMTP protocol conversation (EHLO, AUTH LOGIN, MAIL FROM, RCPT
  TO, DATA) verified against a real local test server — not a mock of
  `smtplib`

### Still open
- **Real Gmail/Outlook inbox verification** — the SMTP conversation is
  proven correct against a real server, but sending to an actual Gmail
  inbox with real credentials hasn't happened yet, and can't happen from
  this development environment (no real credentials were used, by
  design — see `CHANGELOG.md`). This is the next concrete step, to be
  run by whoever owns the sending account
- Scheduled generation + delivery (cron-style) — today, email only goes
  out when `run_daily.py --send-email` is invoked manually
- A delivery failure channel independent of the Daily Brief channel
  itself
- Delivery audit log (what was sent, when, to whom)
- Training Mode digests by email (only the Daily Brief is covered)

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
- **Media & Source Intelligence** — a full architecture is already
  designed (`docs/media-source-intelligence/ARCHITECTURE.md`, Sprint 9.6):
  a scoring and tiering system that learns which sources actually
  generate PR-relevant signal, directly motivated by the Diario
  Financiero finding in Sprint 9.5 (a verified, working feed that
  produced 0/8 relevant stories). Not implemented — design only.
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
