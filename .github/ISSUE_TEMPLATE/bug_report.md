---
name: Bug Report
about: Something in PR HUB behaved incorrectly (code, not a rule/priority judgment call)
title: "[BUG] "
labels: bug
assignees: ''
---

## Description
<!-- What went wrong, in one or two sentences. -->

## Which entry point was affected?
- [ ] `main.py` (single story)
- [ ] `run_daily.py` (Daily Brief)
- [ ] `run_training.py` (Training Mode)
- [ ] Test suite (`pytest`)
- [ ] Other:

## Steps to reproduce
1.
2.
3.

## Input used
<!-- If applicable, paste the noticia.json (or attach it) that triggered
     the bug. If it's a REAL news item you think should also be added to
     training/examples/, say so — that's often the right home for it. -->

```json

```

## Expected behavior
<!-- What should have happened? -->

## Actual behavior
<!-- What actually happened? Include the relevant output/traceback. -->

```

```

## Is this a code bug or a classification disagreement?
- [ ] **Code bug** — the system crashed, produced malformed output, or
      violated an invariant (e.g., detected an entity it shouldn't have,
      like the real "ds inside Ads" substring-matching bug found in
      Sprint 5)
- [ ] **Classification disagreement** — the code ran fine, but you disagree
      with the Priority/Recommendation it produced. **Please use the
      [PR Rule Proposal template](pr_rule_proposal.md) instead** — that's
      a Rulebook conversation, not a bug.

## Environment
- Python version:
- Commit / branch:

## Additional context
<!-- Anything else worth knowing — did this only happen with real news,
     only with a specific brand/competitor, etc. -->
