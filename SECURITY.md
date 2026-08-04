# Security Policy

## Scope

This policy covers the PR HUB codebase in this repository: the Rule
Engine, Knowledge Base, pipeline, Daily Brief generation, and Training
Mode. It does not cover Stellantis Chile's broader corporate infrastructure
— issues with company email, network, or identity systems should go
through standard internal IT Security channels, not this repository.

## Supported versions

| Version | Supported |
|---|---|
| v0.7 (current) | ✅ |
| Pre-release / architecture-spec-only work | ❌ |

As an actively developed internal pilot, only the current version receives
fixes. There is no long-term support branch yet.

## Reporting a vulnerability

PR HUB is an internal repository — please **do not** open a public GitHub
issue for a security concern. Instead:

1. Contact the project maintainer directly (internal Stellantis Chile
   channel — see repository access list / internal directory).
2. Include: what you found, where (file/line if code, or which
   config/rule if a data-exposure concern), and, if possible, how to
   reproduce it.
3. You should receive an acknowledgment within **3 business days**. This
   is a small internal project without a dedicated security team, so
   response times are best-effort, not SLA-backed.

## What counts as a security concern here

Given what this project actually does — classify news and generate an
HTML brief — realistic concerns are narrower than a typical web
application's, but still worth reporting:

- **Data handling**: any path where `training_report.html` or
  `daily_brief.html` could leak information beyond its intended audience
  (e.g., embedding something sensitive from a `noticia.json` field into the
  generated HTML without escaping — see `training/report_renderer.py`'s
  `_esc()` usage as the existing pattern to check against)
- **Dependency risk**: known vulnerabilities in anything listed in
  `requirements.txt`
- **Injection via configuration**: since `config/knowledge_base/*.yml` and
  `config/rules/*.yml` are loaded with `yaml.safe_load` (not `yaml.load`),
  arbitrary YAML should not lead to code execution — a finding that this
  invariant has broken would be a high-priority report
- **Client-side scope of Training Mode**: `training_report.html` runs
  JavaScript locally in the browser (form handling, JSON export via
  `Blob`) and makes **no network calls** by design — a finding that it
  does, or that it could be made to, is a valid and important report (see
  `tests/test_training_report.py::test_report_no_ai_no_network_calls_in_script`
  for the existing guarantee this would violate)

## Out of scope

- Findings that require modifying `config/knowledge_base/` or
  `config/rules/` yourself and observing the (expected) result — those are
  configuration behaving as configured, not a vulnerability
- Social engineering against Stellantis Chile staff
- Denial of service against a local script you're running yourself
