# Changelog

## Research direction clarification

- Reframed the project around action selection in incomplete-information,
  multi-turn tasks, with medical simulation as the initial testbed.
- Added an audit-first roadmap and distinguished future shared-core work from
  existing clinical implementations. No new model calls or performance claims.

## 0.1.0 — research-platform foundation

- Added installable CLI, experiment registry and explicit execution modes.
- Added zero-cost demo artifacts with integrity checks and paired scoring.
- Fixed IG patient-state isolation, final-answer consumption, candidate indexing,
  failure denominators and call estimates; revised checkpoints use fairness-v2.
- Added offline tests, CI and research/provenance documentation.
- Archived the stage diary instead of using it as the project entry point.

No new paid results, local GPU backend or clinical validation are claimed.
Legacy runners have not yet all migrated to one artifact schema.

Validation on the local Python 3.13 environment: 159 tests and 3 subtests
passed (3 dependency deprecation warnings); editable installation, wheel build,
offline demo/report and IG dev dry-run succeeded. No paid calls were made.
Docker build and hosted CI have not been verified for this release.
