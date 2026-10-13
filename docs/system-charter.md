# System Charter

## Purpose

This document defines the charter for the implemented batch governance workflow
and its continuing development: bounded reliability assessment for
machine-learning-based small-business credit underwriting, focused on adverse-action
reason accuracy and traceability and ongoing model-risk oversight.

The system is intended to support model-risk, validation, compliance, and
governance review by turning structured inputs and monitoring logic into
traceable, reviewer-ready outputs.

This evidence engine turns the repository's technical scope into executable
workflow components: schemas, validation checks, monitoring logic, issue records,
reason-review outputs, and evidence-pack artifacts.

## Problem Statement

Governance discussions often remain document-heavy and difficult to
operationalize. Teams may have a framework, checklist, or policy note, but
still lack a repeatable way to:

- validate input records
- compute monitoring metrics
- compare results against configured thresholds
- record breaches and issues
- produce evidence that can be reviewed consistently across time

The implemented workflow addresses these record and review tasks. Its outputs
require assessment against the declared method, data, version, and limitations;
producing a report does not establish model reliability.

## Primary Goal

Maintain a batch, configuration-driven workflow for periodic governance review,
using structured records, declared methods, monitoring protocols, documentation
standards, and portable tools. Synthetic demonstrations and the separate SBA
approved-loan monitoring adapter have distinct data and assessment boundaries.

## Intended Users

- model-risk teams
- validation or effective-challenge reviewers
- compliance and fair-lending reviewers
- governance managers or committees
- internal audit or documentation reviewers
- researchers or practitioners evaluating synthetic demonstrations and bounded
  public-data monitoring methods

## Core Capabilities

- validate structured governance records
- compute monitoring metrics
- identify threshold breaches
- generate issue and breach records
- produce reviewer-ready evidence packs
- preserve traceability across model version, thresholds, explanations, and review outputs

## Non-Objectives

This system is not intended to:

- make credit decisions in production
- provide legal advice or legal conclusions
- certify regulatory compliance automatically
- replace institution-specific validation standards
- claim production deployment or real-world adoption

## Design Principles

- governance-first, not model-first
- configuration-driven rather than hard-coded
- deterministic for the same inputs
- traceable across versions and review events
- explicit about limitations, especially for synthetic data
- narrow in scope to small business underwriting governance

## Implemented Baseline and Continuing Work

The monthly demonstration workflow validates synthetic records, computes
configured metrics, identifies threshold breaches, and emits a reviewable evidence
pack. Linked governance records, reason QA, vendor oversight, and a separate SBA
public-data adapter are also implemented.

The [project overview](../README.md) identifies the current components and
[known target limitations](external-review/targets/v0.12.0.md#disclosed-target-limitations).
Reason-control defects, method-level validation, and scoped independent review
remain substantive work. Supporting screening and optional recourse retain their
separate roles and limitations.
