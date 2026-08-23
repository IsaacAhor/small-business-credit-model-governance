# Repository Roadmap

## Project Anchor

This repository is a standalone technical project for model governance in
machine-learning-based small business credit underwriting. It provides schemas,
workflow code, synthetic fixtures, public-data run kits, and reviewer-ready
outputs for model-risk monitoring, adverse-action reason review, fair-lending
screening triggers, formal validation records, and model-change review. The
model-risk, adverse-action, monitoring, and documentation path is the core;
fair-lending screening is a supporting risk-review module.

All roadmap phases should support that technical scope. The evidence engine is
the implementation vehicle for the repository's workflow and documentation
components.

This roadmap is now paired with `docs/system-implementation-roadmap.md`, which
defines the next technical implementation stage.

The repository should evolve from a framework-and-template artifact into a
credit model governance evidence engine: a batch, configuration-driven system
that validates inputs, runs monitoring checks, records breaches, and generates
reviewer-ready evidence packs.

## Phase 1: Governance Foundation

- establish repository standards
- define the model use case and ownership
- create initial templates for inventory, validation, and change control

## Phase 2: Model Documentation

- document model purpose and decision flow
- record input sources, transformations, and exclusions
- define approval thresholds and override conditions

## Phase 3: Validation and Monitoring

- document validation methodology
- capture performance, stability, and fairness checks
- define monitoring cadence and breach escalation

## Phase 4: Implementation Alignment

- add code or notebook directories once the stack is chosen
- link implementation versions to governance records
- add automated checks relevant to the chosen toolchain

## Phase 5: System Design

- create `docs/system-charter.md`
- create `docs/system-boundaries.md`
- create `docs/control-workflow.md`
- create `docs/domain-object-model.md`
- define users, non-objectives, control events, and evidence-pack outputs

Status:

- Phase 5 documents are now present as the design anchor for the executable system layer.

## Phase 6: Data Contracts

- create JSON schemas for decisions, scores, reason codes, model records,
  thresholds, overrides, outcomes, breaches, and evidence manifests
- add typed Python validation models under `src/credit_gov/`
- create deterministic synthetic demo data aligned to the schemas

Status:

- Phase 6 is now implemented with repository schemas, typed validation models,
  deterministic synthetic demo inputs, and validation tests.

## Phase 7: Executable Governance Workflow

- add a CLI-driven monthly monitoring workflow
- compute approval, score, drift, override, reason-code, and screening metrics
- compare results against configured thresholds
- generate breach records and an evidence pack
- add tests for schema validation and metric logic

Status:

- Phase 7 now has a first executable workflow with monthly monitoring,
  threshold comparison, breach generation, issue generation, adverse-action
  reason QA outputs, fair-lending screening outputs, and reviewer-ready
  evidence-pack generation.

## Phase 8: Domain-Specific Control Extensions

- add adverse-action reason QA and reason generation
- add fair-lending screening, LDA assessment, and escalation outputs
- add model-version change impact reporting
- add vendor model oversight metadata and heightened monitoring mode

Status:

- Adverse-action reason QA, adverse-action reason generation, and the synthetic
  adverse-action reason accuracy benchmark are implemented for demonstration
  inputs.
- Fair-lending screening/escalation and LDA assessment remain implemented as
  separate supporting synthetic demonstration tracks.
- Fair-lending screening now reports statistical significance (two-proportion
  z-test with Fisher's exact fallback) on every disparity screen, and BISG
  protected-class proxy estimation runs as an optional monitoring step with
  posterior-predictive bootstrap and measurement-error sensitivity disparity
  screening (see `docs/fair-lending-statistics.md`).
- A credit-union AI vendor-risk documentation profile is now available under
  `docs/credit-union-ai-vendor-risk-run-kit/`. It maps public NCUA AI,
  third-party-risk, compliance, CUSO, and Regulation B resource themes to due
  diligence, monitoring, adverse-action reason review, model-change review,
  issue tracking, and reviewer signoff.
  The v0.9.2 documentation patch qualified its public sources. The later,
  version-unassigned executable build defined in `IMPLEMENTATION_PLAN.md` is
  now implemented with linked contracts, evidence validation, synthetic
  fixtures, deterministic reporting, and package commands.
- A backward-compatible formal governance bundle is now implemented for model
  risk/materiality, explainability-method assumptions and population boundaries,
  validation independence/findings, and a linked monitoring plan. The repository
  emits a deterministic, hash-verifiable reviewer summary that keeps open gaps
  visible and does not convert self-review into approval.
- The first remaining priority is independent practitioner review and
  method-level validation of the core governance and adverse-action reason path.
  Additional monitoring regression controls follow. Executable vendor
  oversight is implemented but remains synthetic and externally unvalidated.
  Fair-lending/LDA rigor remains supporting work and should not displace those
  core priorities.
