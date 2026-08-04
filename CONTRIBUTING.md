# Contributing to PR HUB

PR HUB is an internal tool, but it's maintained with the same discipline as
a public open-source project: small changes, explicit reasoning, and
nothing merged without tests. This document describes how that works in
practice.

## Before you start

Read [`README.md`](README.md) (architecture + repository structure) and, if
your change touches the Rulebook or Knowledge Base, skim
[`validation_report.md`](validation_report.md) and
[`validation_delta.md`](validation_delta.md) — they're the evidence base
for most recent rule decisions, and your change should either build on that
evidence or explain why it doesn't apply.

## Branch strategy

`main` is always in a working state — every commit on `main` should pass
the full test suite.

Branch names are prefixed by change type:

| Prefix | Use for |
|---|---|
| `feature/...` | New capability (a new pipeline stage, a new report section) |
| `fix/...` | Bug fixes (code logic, not rule/config tuning) |
| `rulebook/...` | Changes scoped to `config/rules/*.yml` only |
| `knowledge-base/...` | Changes scoped to `config/knowledge_base/*.yml` only |
| `docs/...` | Documentation-only changes (like this sprint) |

Rulebook and Knowledge Base changes get their own prefixes deliberately:
they're configuration, not code, and are reviewed differently (see
[PR Rule Proposal template](.github/ISSUE_TEMPLATE/pr_rule_proposal.md) and
[Knowledge Base Update template](.github/ISSUE_TEMPLATE/knowledge_base_update.md)).

## Commit style

Commits are small and descriptive, and **never squashed** — the commit
history is part of the project's documentation. This has been the actual
practice since the project's first sprint; this section formalizes it.

Format: `<Scope>: <imperative description>`

Examples from this repository's real history:
```
P1: agregar Stellantis como organización corporativa en la Knowledge Base
Fix: Entity Recognition usaba matching por subcadena sin límites de palabra
Sprint 5: run_training.py + training/report_renderer.py
Tests: cobertura de daily/aggregator.py y daily/labels.py (14 tests nuevos)
```

- `<Scope>` is a backlog item ID (`P1`, `P3`...), a change type (`Fix`,
  `Tests`, `Docs`), or a sprint label — whatever most precisely identifies
  *why* the commit exists.
- One logical change per commit. A rule change and its test are two
  commits, not one — this makes `git bisect` and code review meaningful.
- Commit messages may be in English or Spanish; this repository has used
  both depending on the sprint. Consistency *within* a PR matters more than
  a single global rule.

## Testing requirements

- The full suite must pass before opening a PR:
  ```bash
  PYTHONPATH=. pytest tests/ -v
  ```
- **Every new rule needs a fixture and a test** demonstrating both that it
  fires when it should, and — where relevant — that it doesn't fire when it
  shouldn't (see `tests/test_brief_generator.py` for the established
  pattern: one positive test, one negative test per rule pair).
- **Every bug fix needs a regression test.** If you found the bug using
  real news (as several bugs in this project's history were), consider
  whether it belongs in `training/examples/` too.
- Code changes to `rule_engine/` require the strongest justification and
  the most scrutiny — see the "Rule Engine changes" note below.

## Pull Request checklist

- [ ] Full test suite passes locally
- [ ] New/changed behavior has a corresponding test
- [ ] Commit messages follow the format above, and are not squashed
- [ ] If a rule changed: linked to a `validation_report.md`/
      `validation_delta.md` finding, or to a new issue using the
      [PR Rule Proposal template](.github/ISSUE_TEMPLATE/pr_rule_proposal.md)
- [ ] If the Knowledge Base changed: confirmed the new entity doesn't
      collide with an existing alias (run the Entity Recognition tests)
- [ ] `README.md` / `ROADMAP.md` updated if the change affects what they
      describe (feature list, status numbers, folder structure)
- [ ] No secrets, API keys, or real customer data committed

## Repository conventions

- **Business logic lives in YAML, not in Python.** If you find yourself
  hardcoding a brand name, priority level, or event type inside
  `rule_engine/`, `classification/`, or `pipeline/`, stop — that almost
  certainly belongs in `config/knowledge_base/` or `config/rules/` instead.
- **The Rule Engine (`rule_engine/`) does not know about Stellantis, PR,
  or automobiles.** It only knows about `Fact`, `Rule`, and `Outcome`. Keep
  it that way — domain concepts belong in the config that's loaded into it,
  not in the engine itself.
- **Every disabled (`enabled: false`) rule must have a `todo:` field**
  explaining exactly what it's blocked on. A disabled rule without a
  documented reason is treated as a bug.
- **Deuda técnica / TODOs are documented inline**, in code comments and in
  the "Deuda técnica" sections of `README.md` — not tracked only in
  someone's memory. If you discover a limitation and don't fix it, write it
  down before you move on.

### Rule Engine changes

`rule_engine/` (the generic condition evaluator, registry, and resolution
strategies) is intentionally the most stable part of this repository — it
has changed only for confirmed bugs, never for business logic, across every
sprint so far. If your change touches this folder, the PR description must
explain why the same outcome isn't achievable through configuration alone.
