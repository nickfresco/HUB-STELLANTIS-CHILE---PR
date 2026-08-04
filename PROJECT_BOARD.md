# Project Board

PR HUB uses a single GitHub Project board to track work across code,
Rulebook, and Knowledge Base changes — all three flow through the same
board, because they go through the same discipline (small change, tests,
review) even though they live in different files.

## Columns

### 📥 Ideas
Anything not yet shaped into a concrete issue — a hunch from reading
`validation_report.md`, a comment on a PR that deserves its own thread, an
observation from a Training Mode session that hasn't been written up yet.
No template required here; this is deliberately low-friction. An item
moves out of Ideas once someone writes it up using the appropriate issue
template (Bug, Feature, PR Rule Proposal, or Knowledge Base Update).

### 📋 Backlog
A written-up issue, using the right template, that is not yet scheduled.
This is where `validation_report.md`'s Sprint Backlog table and
`ROADMAP.md`'s "Planned" items should have a corresponding card — the
board is the operational view of the same priorities those documents
already describe; if the board and those documents disagree about
priority, that's worth resolving explicitly, not just picking one silently.

### 🔨 In Progress
Actively being worked on, with a branch open (see `CONTRIBUTING.md` for
branch naming). One person "owns" the card while it's here — if it stalls,
it moves back to Backlog rather than sitting here indefinitely.

### 🧪 Testing
Code/config is complete and pushed; the full suite passes locally; but it
hasn't yet cleared the specific verification the change type requires:

- **Code changes:** PR open, awaiting review
- **Rule/Knowledge Base changes:** awaiting a Training Mode validation
  pass (see the `needs-validation` label) — a rule that "looks right" and
  a rule that's been checked against real news are different states, and
  this column is where that difference is tracked
- **Documentation changes:** awaiting a read-through for accuracy (numbers,
  file paths, and claims about "what exists" go stale fast in a fast-moving
  repo — see this same Sprint 8 as an example of a documentation-only
  change that still needed verified figures)

### ✅ Done
Merged to `main`. For Rulebook/Knowledge Base changes specifically, "Done"
also means the change is reflected in the next `validation_delta.md` (or
queued for the next one), so the evidence trail stays connected — a merged
rule change isn't fully done until its effect has been measured.

## How this maps to issue templates

| Card originates from | Typical path |
|---|---|
| [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) | Ideas → Backlog → In Progress → Testing (review) → Done |
| [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) | Ideas → Backlog → In Progress → Testing (review) → Done |
| [PR Rule Proposal](.github/ISSUE_TEMPLATE/pr_rule_proposal.md) | Ideas → Backlog → In Progress → **Testing (Training Mode validation)** → Done |
| [Knowledge Base Update](.github/ISSUE_TEMPLATE/knowledge_base_update.md) | Ideas → Backlog → In Progress → **Testing (alias collision + validation)** → Done |

## What this board is not

It's not a replacement for `ROADMAP.md` (which describes *versions and
objectives*) or `validation_report.md` / `validation_delta.md` (which
describe *evidence*). The board tracks the day-to-day movement of
individual pieces of work; those documents remain the source of truth for
why a piece of work exists and whether it worked.
