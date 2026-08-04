# GitHub Labels

Proposed label set for PR HUB. Colors follow a rough convention: red/orange
for urgency and problems, blue/purple for engine and process, green for
approachability, gray for meta.

To create these via the `gh` CLI once the repository is on GitHub:

```bash
gh label create "bug" --color "d73a4a" --description "Something isn't working as coded"
gh label create "enhancement" --color "a2eeef" --description "New feature or structural improvement"
gh label create "documentation" --color "0075ca" --description "README, ROADMAP, or other docs"
gh label create "training" --color "5319e7" --description "Training Mode: validation workflow, reports, real-news examples"
gh label create "knowledge-base" --color "1d76db" --description "Brands, Competitors, Organizations, Sources, Products, Taxonomy"
gh label create "rule-engine" --color "0e8a16" --description "config/rules/*.yml or rule_engine/ itself"
gh label create "good first issue" --color "7057ff" --description "Well-scoped, good entry point for a new contributor"
gh label create "priority-high" --color "b60205" --description "Should be addressed in the current or next sprint"
gh label create "priority-medium" --color "fbca04" --description "Worth doing, not urgent"
gh label create "priority-low" --color "c5def5" --description "Nice to have, no rush"
gh label create "needs-validation" --color "e99695" --description "Requires a real-news Training Mode round before merging"
gh label create "backlog" --color "ededed" --description "Tracked in validation_report.md / validation_delta.md, not yet scheduled"
```

## Full list

| Label | Color | Description |
|---|---|---|
| `bug` | `#d73a4a` | Something isn't working as coded — see [Bug Report template](ISSUE_TEMPLATE/bug_report.md) |
| `enhancement` | `#a2eeef` | New feature or structural improvement — see [Feature Request template](ISSUE_TEMPLATE/feature_request.md) |
| `documentation` | `#0075ca` | README, ROADMAP, CONTRIBUTING, or other docs |
| `training` | `#5319e7` | Training Mode: the validation workflow, HTML reports, or `training/examples/` |
| `knowledge-base` | `#1d76db` | Brands, Competitors, Organizations, Sources, Products, or Taxonomy — see [KB Update template](ISSUE_TEMPLATE/knowledge_base_update.md) |
| `rule-engine` | `#0e8a16` | `config/rules/*.yml` (a rule proposal) or `rule_engine/` itself (the generic engine code) — see [PR Rule Proposal template](ISSUE_TEMPLATE/pr_rule_proposal.md) |
| `good first issue` | `#7057ff` | Well-scoped, good entry point for a new contributor |
| `priority-high` | `#b60205` | Should be addressed in the current or next sprint |
| `priority-medium` | `#fbca04` | Worth doing, not urgent |
| `priority-low` | `#c5def5` | Nice to have, no rush |
| `needs-validation` | `#e99695` | A rule/KB change that should go through a real-news Training Mode round before being considered done |
| `backlog` | `#ededed` | Already tracked in `validation_report.md` or `validation_delta.md`, not yet scheduled into a sprint |

## Usage notes

- `rule-engine` and `knowledge-base` are **not** interchangeable —
  `rule-engine` implies a change to `config/rules/` or, rarely, to
  `rule_engine/` itself; `knowledge-base` implies a change to
  `config/knowledge_base/`. A single issue can carry both if it needs
  both (that's common — see `PR-016` and `PR-017`, which needed a
  Knowledge Base entity *and* two new rules).
- `needs-validation` exists because this project's own history shows that
  rule changes that look obviously correct can still be wrong in practice
  (see `validation_report.md`) — it's a process label, not a severity
  label, meant to be paired with `rule-engine`.
- Priority labels (`priority-high/medium/low`) mirror the priority
  vocabulary already used in `validation_report.md`'s Sprint Backlog table,
  intentionally, so an issue's label and its position in that table stay
  legible against each other.
