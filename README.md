```
████  ████      █   █ █   █ ████  
█   █ █   █     █   █ █   █ █   █ 
█   █ █   █     █████ █   █ █   █ 
████  ████      █   █ █   █ ████  
█     █  █      █   █ █   █ █   █ 
█     █   █     █   █  ███  ████  
```

<p align="center"><strong>Automated PR Intelligence Platform for Stellantis Chile</strong></p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.7-blue">
  <img alt="Tests" src="https://img.shields.io/badge/tests-74%20passing-brightgreen">
  <img alt="Rulebook" src="https://img.shields.io/badge/rulebook-10%2F17%20rules%20active-yellow">
  <img alt="Status" src="https://img.shields.io/badge/status-internal%20pilot-orange">
  <img alt="License" src="https://img.shields.io/badge/license-internal%20%2F%20proprietary-lightgrey">
</p>

---

## Overview

**PR HUB** is a rule-based decision engine that turns raw automotive-industry
news into a structured, prioritized daily briefing for the PR & Corporate
Communications team at **Stellantis Chile**.

Every morning, a Communications Coordinator needs to answer four questions in
under two minutes:

1. What happened?
2. What needs attention today?
3. What opportunities exist?
4. What should I do about it?

PR HUB exists to answer those four questions automatically, from real news,
**without AI-generated judgment calls**. Every classification — brand,
event type, priority, recommendation — is produced by a deterministic,
YAML-configured Rule Engine that a human can read, audit, and correct. There
is no black box: every decision the system makes can be traced back to the
exact rule that produced it.

**Who it's for:** the PR Coordinator who currently has to read a dozen news
sites every morning, and whoever maintains PR HUB's Knowledge Base and
Rulebook as the business evolves.

**Why not just use an LLM to read the news and decide?** Because the whole
point of a decision-support tool for a communications team is that its
judgment has to be *explainable and correctable* — "the AI thought this was
important" is not an acceptable answer when a journalist calls. PR HUB's
core design principle, since its first architectural discussion, has been:
**the model may draft language later; it does not decide priority.** That
boundary is enforced by construction, not by convention — see
[`rule_engine/`](rule_engine/) and [`ARCHITECTURE`](#architecture) below.

---

## Features

- ✓ **Rule Engine** — generic, domain-agnostic, YAML-driven condition/outcome evaluator (AND/OR/NOT, `single_winner` / `accumulate_all` resolution)
- ✓ **Knowledge Base** — Brands, Competitors, Organizations, Products, Sources, Taxonomy, Event Types (all in `config/knowledge_base/`)
- ✓ **Entity Recognition** — deterministic alias matching with word-boundary safety and disambiguation context (no NLP, no probabilistic models)
- ✓ **Event Detection** — keyword-based inference of event type when not explicitly provided
- ✓ **Priority Engine** — 17 configured rules (10 active, 7 documented as pending on explicit dependencies)
- ✓ **Recommendation Engine** — maps classified stories to a closed catalog of 9 PR actions
- ✓ **Daily Brief** — generates a client-safe (Gmail/Outlook-compatible) HTML executive brief
- ✓ **Training Mode** — a human-in-the-loop validation workflow: run real news through the system, mark each classification correct/incorrect, export the verdicts as JSON
- ✓ **Validation Workflow** — structured analysis (`validation_report.md`, `validation_delta.md`) that turns human corrections into a prioritized, evidence-based improvement backlog
- ✓ **HTML Reports** — `daily_brief.html`, `training_report.html`, both self-contained, no server required

> **Not yet implemented:** automated ingestion (RSS/alerts), scheduled email
> delivery, sentiment analysis, and multi-tenant support. These are staged on
> the [Roadmap](ROADMAP.md), not silently missing — every gap here is a
> tracked, documented decision, not an oversight.

---

## Architecture

```mermaid
flowchart TD
    A["News Input · JSON"] --> B["Entity Recognition"]
    B --> C["Event Detection"]
    C --> D["Priority Rule Engine"]
    D --> E["Recommendation Engine"]
    E --> F["Daily Brief Generator"]
    F --> G["daily_brief.html"]

    KB[("Knowledge Base<br/>brands · competitors · organizations<br/>sources · taxonomy · event types")] -.-> B
    KB -.-> C
    RB[("Rulebook<br/>priority_rules.yml<br/>recommendation_rules.yml")] -.-> D
    RB -.-> E

    F --> T["Training Mode"]
    T --> H["training_report.html"]
    H --> V["Human Validation"]
    V --> J["training_validations.json"]
    J --> AN["Validation Analysis"]
    AN --> RB
```

Each stage is an independently swappable pipeline component (see
[`pipeline/stages.py`](pipeline/stages.py)) — Entity Recognition can be
replaced by a more advanced component later without touching Event
Detection, the Rule Engine, or anything downstream. This isn't aspirational:
it's demonstrated in `tests/test_pipeline.py`, which swaps a stage for a
fake implementation mid-test.

The dotted lines are intentional: the Knowledge Base and the Rulebook are
**configuration**, not code. Nothing in `rule_engine/` knows what
"Stellantis" or "Peugeot" means — see
[Repository Structure](#repository-structure) below.

---

## Repository Structure

```
pr-hub/
├── config/
│   ├── knowledge_base/     # brands, competitors, organizations, models,
│   │                       # technologies, sources, taxonomy, event_types
│   └── rules/               # priority_rules.yml, recommendation_rules.yml
├── knowledge_base/          # Knowledge Base Loader (Python)
├── rule_engine/              # Generic, domain-agnostic engine: condition,
│                             # rules, loader, registry, evaluation
├── classification/           # Entity Recognition + Event Detection
├── models/                   # NewsInput dataclass, domain enums
├── pipeline/                  # Decoupled pipeline stages + orchestrator
├── brief/                     # Daily Brief Generator (pure functions, per story)
├── daily/                     # Aggregation, labels, email-safe HTML renderer
├── training/                  # Training Mode: report renderer + validations archive
│   ├── examples/              # 16 REAL news items (Jul/Aug 2026) used for validation
│   └── validations/           # Archived human-validation rounds (JSON)
├── data/daily_input/          # Fictional news samples for demoing the Daily Brief
├── examples/                  # Fictional news samples for demoing main.py
├── tests/                     # 74 automated tests + fixtures
├── .github/                   # Issue templates, label proposal
├── main.py                    # Single-story CLI: python main.py noticia.json
├── run_daily.py                # Batch CLI: python run_daily.py
├── run_training.py             # Training Mode CLI: python run_training.py
├── validation_report.md        # Round 1 analysis (accuracy, root causes, backlog)
├── validation_delta.md         # Round 1 → post-fix comparison
├── ROADMAP.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── LICENSE
```

---

## Quick Start

**Install:**

```bash
pip install -r requirements.txt
```

**Run the test suite:**

```bash
PYTHONPATH=. pytest tests/ -v
```

**Generate a Daily Brief** (fictional sample data, `data/daily_input/`):

```bash
python run_daily.py
# → daily_brief.html
```

**Classify a single news item:**

```bash
python main.py examples/ejemplo_recall_con_impacto_chile.json
```

**Run Training Mode** (16 real news items, `training/examples/`):

```bash
python run_training.py
# → training_daily_brief.html
# → training_report.html   (open this one — mark each story Sí/No,
#                            then "Descargar validaciones" for the record)
```

See [`config/knowledge_base/`](config/knowledge_base) and
[`config/rules/`](config/rules) for the full YAML input schema, and each
folder's module docstring for design notes and known limitations.

---

## Current Status

| | |
|---|---|
| **Version** | v0.7 |
| **Automated tests** | 74 passing, 0 failing |
| **Rulebook coverage** | 10 of 17 rules active (7 documented as pending, each with an explicit blocking dependency) |
| **Estimated accuracy** | ~75% (post-fix estimate against Round 1 of real-news validation — see [`validation_delta.md`](validation_delta.md); a Round 2 with fresh human validation is the next recommended step, not yet run) |
| **Project maturity** | **Internal pilot.** Core decision engine and validation loop are stable and tested; ingestion, delivery, and sentiment analysis are not yet built (see [Roadmap](ROADMAP.md)) |

---

## Roadmap

See [`ROADMAP.md`](ROADMAP.md) for the full plan from v0.7 (current) through
v1.0 (production-ready).

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for branch strategy, commit
conventions, testing requirements, and the PR checklist. See also
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) and
[`SECURITY.md`](SECURITY.md).

---

<p align="center"><sub>PR HUB is an internal tool built for the Stellantis Chile PR & Corporate Communications team. It is not affiliated with, endorsed by, or representing the official Stellantis brand identity.</sub></p>
