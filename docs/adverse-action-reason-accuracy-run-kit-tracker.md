# Adverse-Action Reason Accuracy and Transparency Run Kit Tracker

## Workstream Name

Adverse-action reason accuracy and transparency under Regulation B 12 CFR
1002.9.

Do not use the internal shorthand "CORE 2" in reviewer-facing repository
artifacts.

## Purpose

This tracker controls the build sequence for a public run kit that demonstrates
reason generation, driver-to-reason mapping, reason-code QA, and evidence-pack
review workflow for adverse-action reason accuracy and transparency.

The public proof path is synthetic small-business credit data. Public datasets
can support context or off-domain mechanics only. A real-world accuracy claim
requires private, deidentified lender/CDFI/fintech data with declined
applications, disclosed reasons or notices, actual decision drivers, mapping
versions, and reviewer labels.

## Current Status

Status: implementation, focused validation, scoped commit, and public branch push complete.

Branch: `adverse-action-reason-run-kit`

Pre-existing local changes not part of this tracker:

- `scripts/make_sba_fixture.py`
- `scripts/sba_to_monitoring.py`

Do not include those files in commits for this workstream unless they are
separately reviewed and intentionally brought into scope.

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

The run kit is not done until all of the following are true:

- method and limitation documents are present
- synthetic benchmark inputs are present and documented
- run script or workflow entry point is present
- generated example evidence pack is present
- tests cover the benchmark and expected QA failures
- repository guardrails pass
- release notes identify what the milestone demonstrates and what it does not
  prove
- unrelated local changes are excluded from the commit
- public sync is completed by pushing the scoped branch or merged release commit

Do not mark a checklist item complete unless its files exist and its validation
or review gate has passed.

## Build Checklist

- [x] Confirm descriptive workstream name and public proof limitation.
- [x] Add method note:
  `docs/adverse-action-reason-accuracy-method.md`
- [x] Add public-data limitation note:
  `docs/adverse-action-public-data-limitations.md`
- [x] Add private-data field specification:
  `docs/private-data-spec-adverse-action-reasons.md`
- [x] Add synthetic benchmark dataset:
  `data/synthetic/adverse-action-reason-benchmark/`
- [x] Add benchmark run script:
  `scripts/run_adverse_action_reason_benchmark.py`
- [x] Add curated example evidence pack:
  `examples/evidence-packs/adverse-action-reason-benchmark/`
- [x] Add or update tests for benchmark generation, QA exceptions, and evidence
  outputs.
- [x] Update reviewer entry points only after the benchmark and evidence pack
  are working.
- [x] Add release note for the next milestone.
- [x] Run focused tests and repository guardrails.
- [x] Commit only scoped adverse-action files.
- [x] Push branch to the public remote.

## Synthetic Benchmark Requirements

The benchmark should include clean declined-decision cases plus seeded failures:

- missing reason output for a declined decision
- generic reason text
- unmapped reason code
- driver-to-mapping mismatch
- stale mapping version
- reason output attached to a non-declined decision
- declined decision with no mapped adverse driver
- excessive reason count for a single declined decision
- FCRA-only or credit-report-only placeholder that does not satisfy the
  adverse-action reason mapping standard

The benchmark should preserve the current repository discipline: synthetic
status is explicit, outputs are deterministic, and QA results are review
triggers rather than legal conclusions.

## Public-Data Rule

SBA 7(a), PPP, and CRA data cannot prove adverse-action reason accuracy because
they do not provide the complete chain of declined applications, disclosed
reasons or notices, actual decision drivers, and review labels.

HMDA may be used only as an off-domain mortgage-denial reason-code mechanics
proxy. It should not be described as small-business credit proof.

## Release Sequence

- `v0.8.0`: synthetic adverse-action reason benchmark and evidence pack
- `v0.8.1`: method note, limitation note, and reviewer packaging updates
- `v0.9.0`: optional HMDA off-domain mechanics proxy
- `v0.9.1`: private-data specification and deidentification checklist
- `v1.0.0`: only after external practitioner/counsel review or private-data
  pilot evidence supports a stronger milestone
