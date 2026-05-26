# Repository Roadmap

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

## Phase 7: Executable Governance Workflow

- add a CLI-driven monthly monitoring workflow
- compute approval, score, drift, override, reason-code, and screening metrics
- compare results against configured thresholds
- generate breach records and an evidence pack
- add tests for schema validation and metric logic

## Phase 8: Domain-Specific Control Extensions

- add adverse-action reason QA
- add fair-lending screening and escalation outputs
- add model-version change impact reporting
- add vendor model oversight metadata and heightened monitoring mode
