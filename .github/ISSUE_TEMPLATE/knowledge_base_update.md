---
name: Knowledge Base Update
about: Add or update a Brand, Competitor, Organization, Product, Source, or Event Type
title: "[KB] "
labels: knowledge-base
assignees: ''
---

## Which file does this affect?
- [ ] `brands.yml` (Stellantis sub-brands only)
- [ ] `competitors.yml`
- [ ] `organizations.yml`
- [ ] `models.yml` / `technologies.yml` (Products)
- [ ] `sources.yml`
- [ ] `taxonomy.yml` (Category / Subcategory)
- [ ] `event_types.yml`

## Change type
- [ ] Add a new entity
- [ ] Update an existing entity (alias, metadata, active status)
- [ ] Deactivate an entity (`active: false` — prefer this over deleting)

## Proposed entry

```yaml
canonicalId:
displayName:
aliases:
  -
active: true
```

For a **Source**, also include: `tier`, `type`, `country`,
`acquisition_method`.
For a **Product**, also include: `type` (Modelo / Plataforma / Motor /
Tecnología / ADAS / Batería).
For an **Organization**, also include: `organization_type`.

## Justification / evidence
<!-- Why does this need to exist? Link a real news item (ideally one that
     could go in training/examples/) where this entity is mentioned but
     not currently detected. -->

## Alias collision check
<!-- Have you checked this alias doesn't overlap with an existing entity?
     (Real example from this project: "Jeep" as a bare word required a
     disambiguationContext because it's also a generic Spanish word for
     off-road vehicle — see brands.yml.) If the alias is short, common, or
     could appear inside another word, propose a `disambiguationContext`. -->

- [ ] Checked — no collision found
- [ ] Collision found — proposed `disambiguationContext`:

## Does this unblock a PENDING rule?
<!-- Check config/rules/priority_rules.yml and recommendation_rules.yml
     for rules with enabled: false whose `todo:` mentions a missing
     Knowledge Base entity (e.g., PR-015 is blocked on Person not
     existing as a catalog). If this KB update unblocks one, link it. -->
