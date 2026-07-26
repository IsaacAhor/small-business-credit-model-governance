# Release Strategy

## Purpose

This repository uses versioned releases to mark stable public milestones, not
just development commits. A release identifies a coherent review point that can
be inspected, cited, downloaded, or preserved as evidence of progress.

Commits remain useful for development history. Releases serve a different role:
they package the state of the work at meaningful implementation milestones.

## Release Principles

- Releases should map to completed implementation phases or major reviewer-facing
  packaging milestones.
- Releases should preserve synthetic demonstration artifacts and their limits.
- Releases should not imply production deployment, lender adoption, legal
  conclusions, or regulatory approval.
- Release notes should identify what the release demonstrates and what it does
  not prove.
- Future phases should be released only after tests and repository guardrails
  pass through the normal GitHub workflow.

## Version Naming

Use semantic-style version numbers for public milestones:

- `v0.1.0`: data contracts and synthetic validation baseline
- `v0.2.0`: monthly monitoring evidence run
- `v0.3.0`: adverse-action reason QA workflow
- `v0.4.0`: fair-lending screening and reviewer-facing evidence package
- `v0.4.1`: outsider packaging patch with reviewer and implementation guides
- `v0.5.0`: adverse-action reason generation, LDA assessment, and portfolio-scale dataset
- `v0.6.0`: statistical significance testing and BISG proxy monitoring
- `v0.7.0`: SBA 7(a) public-data monitoring run kit
- `v0.8.0`: synthetic adverse-action reason accuracy benchmark

The `0.x` version line signals that this is still a public demonstration and
governance evidence engine under active development, not a production release.

Patch releases can be used for material packaging, documentation, or
reviewability improvements that do not change the implementation phase.

## Current Release

The first versioned milestone was `v0.4.0`, because the repository contained
Phases 0 through 4:

- system design and governance charter
- data contracts and synthetic validation
- cross-file evidence-integrity validation
- monthly monitoring evidence-pack generation
- adverse-action reason QA
- fair-lending screening and escalation outputs
- reviewer-facing project packaging and example evidence outputs

The current documented milestone is `v0.8.0`, which adds the synthetic adverse-
action reason accuracy benchmark: a public, on-domain run kit for reason
generation, driver-to-reason mapping, reason QA, benchmark-specific exception
checks, and reviewer-ready evidence packaging under Regulation B 12 CFR 1002.9.
The milestone demonstrates a reproducible method and public-data boundary; it
is not proof of live small-business adverse-action notice accuracy, lender
adoption, legal compliance, external validation, regulatory approval, or field
recognition.

The prior milestone, `v0.7.0`, adds the SBA 7(a) public-data monitoring run kit:
an adapter for real SBA 7(a)/504 FOIA loan-level data, a synthetic schema
fixture for pipeline validation, reproducibility documentation, and
scope/limitations notes. The run kit is a model-risk monitoring and drift-
reporting exercise on real approved-loan public data; it is not an underwriting
model, fairness analysis, adverse-action analysis, lender adoption, legal
conclusion, or regulatory acceptance.

The prior substantive analytical milestone, `v0.6.0`, adds statistical
significance testing to fair-lending disparity screens and optional BISG
protected-class proxy monitoring on the portfolio-scale synthetic dataset. The
repository also contains a Phase 5 model-change and validation-review workflow,
but that workflow should not be described as the `v0.7.0` GitHub release
milestone.

## Release Notes Location

Release notes are stored under `docs/releases/`. Each release note should be
short, reviewer-readable, and disciplined about limitations.

## Evidence Discipline

Versioned releases can support the record by showing execution history,
implementation maturity, and stable public artifacts. They do not by themselves
prove external recognition, production deployment, institutional adoption, or
regulatory acceptance.
