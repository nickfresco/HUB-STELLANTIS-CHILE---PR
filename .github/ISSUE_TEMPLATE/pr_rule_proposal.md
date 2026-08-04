---
name: PR Rule Proposal
about: Propose a new rule, or a change to an existing rule, in priority_rules.yml / recommendation_rules.yml
title: "[RULE] "
labels: rule-engine
assignees: ''
---

## Real example driving this proposal
<!-- PR HUB's rules are built from real cases, not hypotheticals — every
     existing rule traces back to either a documented real news item or a
     Training Mode validation finding. Provide one here. -->

**Story:** <!-- headline -->
**Source:** <!-- outlet, and URL if available -->
**Link to evidence (if any):** <!-- a `training/examples/*.json` file, or
     a specific entry in `training/validations/round_N.json`, or a finding
     in `validation_report.md` -->

## Current behavior
<!-- What does the system do today with a story like this? Which rule (if
     any) fires? Run it through `main.py` and paste the output. -->

```json

```

## Desired behavior

**Condition** (which entities / event type should trigger this):
- Brands:
- Competitors:
- Organizations:
- Event Type:
- Other condition fields:

**Priority:** `Critical` / `High` / `Medium` / `Low`

**Recommendation(s):** <!-- must be values from the existing catalog
     unless this proposal also requests expanding it — see "Catalog
     impact" below -->
- [ ] EvaluarComunicado
- [ ] EvaluarQyA
- [ ] EvaluarComiteDeCrisis
- [ ] InformarBrandManager
- [ ] EvaluarPlanDeDifusion
- [ ] CompartirAnalisisCompetitivo
- [ ] MonitorearEvolucion
- [ ] EvaluarOportunidadDeContenido
- [ ] SinAccionInmediata

## Does this overlap with an existing rule?
<!-- Check config/rules/priority_rules.yml for a rule with a similar
     condition. If one exists, explain whether this should replace it,
     narrow it (like PR-013 was split into PR-013 + PR-017), or coexist
     with it. -->

## Catalog impact
- [ ] This proposal fits entirely within the existing
      `RecommendationAction` catalog (9 values)
- [ ] This proposal needs a new value in the catalog — explain why an
      existing value doesn't fit, and flag this explicitly for a
      **business conversation before implementation** (see
      `validation_report.md`, item P7, for the precedent on why this
      isn't done unilaterally)

## Knowledge Base impact
- [ ] All entities referenced already exist in `config/knowledge_base/`
- [ ] This proposal also requires a
      [Knowledge Base Update](knowledge_base_update.md) — link it here
