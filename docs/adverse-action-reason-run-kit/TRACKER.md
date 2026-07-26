# Adverse-Action Reason Run Kit Tracker

## Workstream Name

Adverse-action reason accuracy and transparency under Regulation B 12 CFR
1002.9.

## Purpose

This tracker controls the adverse-action reason run kit. The run kit gives a
first-time reviewer one folder for the benchmark method, public-data limits,
private-data requirements, evidence-pack review path, and build status while
leaving executable code, synthetic data, tests, and generated evidence packs in
their normal repository locations.

## Status

Status: complete for the synthetic benchmark, landing-folder packaging, focused
local validation, and documentation consolidation.

The canonical documentation folder is:

```text
docs/adverse-action-reason-run-kit/
```

## Canonical Files

| File | Purpose |
| --- | --- |
| `README.md` | Reviewer and operator start point |
| `METHOD.md` | Method note for reason generation, mapping, QA, and evidence packaging |
| `PUBLIC_DATA_LIMITS.md` | Public-data boundary for SBA, PPP, CRA, HMDA, and 1071 context |
| `PRIVATE_DATA_SPEC.md` | Full deidentified private-data field specification |
| `PRIVATE_DATA_REQUIREMENTS.md` | Short private-data landing summary |
| `BENCHMARK_SPEC.md` | Synthetic benchmark inputs, seeded defects, and expected checks |
| `EVIDENCE_PACK_REVIEW.md` | How to inspect the generated evidence pack |
| `LIMITATIONS.md` | Scope, candor rules, and overclaims to avoid |
| `TRACKER.md` | Build status and remaining evidence gaps |

## Scope Discipline

This workstream is limited to adverse-action reason accuracy and transparency.

In scope:

- declined-decision reason generation
- decision-driver to reason-code mapping
- reason-code mapping version control
- reason QA exceptions
- reviewer-ready evidence packs
- public-data limitation documentation
- private-data field specification
- optional HMDA denial-reason mechanics proxy, clearly labeled off-domain

Out of scope:

- general fair-lending screening
- less-discriminatory-alternative assessment
- federal ECOA disparate-impact or effects-test framing
- SBA/PPP/CRA as proof of adverse-action reason accuracy
- claims of deployment, adoption, regulatory approval, legal compliance, or
  external validation without independent evidence

## Done Definition

The run kit is done when all of the following are true:

- one-folder entry point exists under `docs/adverse-action-reason-run-kit/`
- method, public-data limit, and private-data specification docs are inside the
  kit folder
- README gives purpose, scope, exact run command, validation commands, and
  review sequence
- limitations do not overclaim public proof
- benchmark specification explains inputs, seeded defects, and success criteria
- evidence-pack review note explains how to inspect generated outputs
- synthetic benchmark inputs are present and documented
- benchmark run script is present
- generated example evidence pack is present
- tests cover the benchmark and expected QA failures
- repository guardrails pass
- release notes identify what the milestone demonstrates and what it does not
  prove

## Checklist

- [x] Create landing folder.
- [x] Add `README.md`.
- [x] Add `METHOD.md`.
- [x] Add `PUBLIC_DATA_LIMITS.md`.
- [x] Add `PRIVATE_DATA_SPEC.md`.
- [x] Add `LIMITATIONS.md`.
- [x] Add `BENCHMARK_SPEC.md`.
- [x] Add `EVIDENCE_PACK_REVIEW.md`.
- [x] Add `PRIVATE_DATA_REQUIREMENTS.md`.
- [x] Add tracker.
- [x] Move standalone adverse-action docs into the kit folder.
- [x] Remove duplicate top-level adverse-action tracker.
- [x] Update root reviewer entry points and evidence map.
- [x] Run focused benchmark test.
- [x] Run benchmark regeneration command.
- [x] Run repository guardrails.
- [x] Keep release changes scoped to adverse-action run kit artifacts.

## Public-Data Rule

SBA 7(a), PPP, and CRA data cannot prove adverse-action reason accuracy because
they do not provide the complete chain of declined applications, disclosed
reasons or notices, actual decision drivers, and review labels.

HMDA may be used only as an off-domain mortgage-denial reason-code mechanics
proxy. It should not be described as small-business credit proof.

## Candor Notes

The adverse-action benchmark remains synthetic. Public small-business data still
cannot prove real-world adverse-action reason accuracy because it lacks declined
applications, actual decision drivers, disclosed reasons or notice text, reason
mapping versions, and reviewer labels.

The strongest truthful claim is that the repository provides a reproducible
synthetic benchmark and reviewer-ready evidence-pack method for adverse-action
reason accuracy and transparency review.
