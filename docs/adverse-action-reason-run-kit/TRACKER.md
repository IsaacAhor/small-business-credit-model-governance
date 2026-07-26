# Adverse-Action Reason Run Kit Landing Tracker

## Workstream Name

Adverse-action reason accuracy and transparency under Regulation B 12 CFR
1002.9.

Do not use the internal shorthand "CORE 2" in reviewer-facing artifacts.

## Purpose

This tracker controls the landing-folder packaging layer for the existing
synthetic adverse-action reason benchmark. The goal is to give a first-time
reviewer one obvious place to start while preserving canonical code, data,
tests, and generated outputs in their normal repository locations.

## Status

Status: complete for landing-folder build and focused local validation. Public sync is evidenced by the merge commit that contains this tracker.

Branch: `adverse-action-run-kit-landing`

Pre-existing local changes excluded from this workstream:

- `scripts/make_sba_fixture.py`
- `scripts/sba_to_monitoring.py`

## Done Definition

The landing run kit is done when all of the following are true:

- one-folder entry point exists under `docs/adverse-action-reason-run-kit/`
- README gives purpose, scope, exact run command, validation commands, and
  review sequence
- limitations are in the landing folder and do not overclaim public proof
- benchmark specification explains inputs, seeded defects, and success criteria
- evidence-pack review note explains how to inspect generated outputs
- private-data requirements are summarized and linked to the canonical spec
- root reviewer entry points link to the landing folder
- focused benchmark test passes
- repository guardrails pass
- scoped commit excludes unrelated SBA worktree changes
- public sync is completed through the normal GitHub workflow

## Checklist

- [x] Create landing folder.
- [x] Add `README.md`.
- [x] Add `LIMITATIONS.md`.
- [x] Add `BENCHMARK_SPEC.md`.
- [x] Add `EVIDENCE_PACK_REVIEW.md`.
- [x] Add `PRIVATE_DATA_REQUIREMENTS.md`.
- [x] Add tracker.
- [x] Update root reviewer entry points.
- [x] Run focused benchmark test.
- [x] Run benchmark regeneration command.
- [x] Run repository guardrails.
- [x] Commit only scoped landing-folder and reviewer-entrypoint files.
- [x] Push branch and complete public sync.

## Candor Notes

The landing folder improves reviewability. It does not change the proof level.
The adverse-action benchmark remains synthetic. Public small-business data still
cannot prove real-world adverse-action reason accuracy because it lacks
declined applications, actual decision drivers, disclosed reasons or notice
text, reason mapping versions, and reviewer labels.
