# Framework Outline

## Working Title

Interpretable Model-Risk Governance Framework for Machine-Learning-Based Small Business Credit Underwriting

## Purpose

This document outlines a practical framework for governing, monitoring, and documenting machine-learning-based small business credit underwriting systems. It centers model-risk oversight, adverse-action reason traceability, explanation-method governance, and reviewer-ready evidence. Disparity screening is a supporting risk-review component.

## Problem Statement

Small business credit underwriting increasingly relies on analytical systems that may be difficult to interpret, monitor, and justify when adverse decisions must be explained. A governance framework is needed to help institutions document decisions, trace reasons through the governed decision process, monitor model risk, assess explanation-method limitations, and preserve reviewable evidence over time.

## Target Users

- lender model-risk teams
- credit risk and analytics teams
- compliance and fair-lending functions reviewing supporting risk screens
- internal audit and governance reviewers
- fintech teams building or monitoring underwriting systems

## Framework Objectives

- define core governance requirements for ML-based small business underwriting
- establish monitoring categories for performance, drift, explanation quality, and change control
- support adverse-action reason mapping, traceability, and notice review
- retain disparity and alternative assessment as optional supporting risk-review modules
- provide reusable documentation and oversight checkpoints

## Proposed Sections

### 1. Introduction

- scope of small business credit underwriting
- why ML governance in this use case is distinct
- need for transparency, oversight, and disciplined monitoring

### 2. System Scope and Risk Boundaries

- product and portfolio definition
- model purpose and decision context
- use limitations and governance boundaries
- stakeholders and oversight roles

### 3. Governance Architecture

- model ownership
- challenge and validation roles
- approval and escalation structure
- documentation minimums

### 4. Adverse-Action and Explainability Controls

- explanation design principles
- reason-code mapping logic
- explanation stability and consistency review
- adverse action explanation considerations

### 5. Performance and Drift Monitoring

- model performance metrics
- population drift indicators
- feature drift indicators
- override and exception monitoring

### 6. Reporting and Escalation

- management reporting cadence
- issue logging
- remediation ownership
- board or committee escalation thresholds

### 7. Supporting Disparity-Risk Screening

- segmentation logic
- disparity screening
- threshold governance
- optional alternative-review triggers where the applicable legal and policy
  context supports them

### 8. Change Management

- version control
- retraining triggers
- model updates and approvals
- documentation refresh rules

### 9. Implementation Checklist

- pre-deployment controls
- post-deployment monitoring controls
- periodic review controls

### 10. Limitations and Extensions

- proxy data limitations
- explainability tradeoffs
- portfolio-specific customization
- future research and tooling extensions

## Suggested Output Format

- publishable PDF framework
- shorter executive summary
- implementation checklist in template form
- notebook or prototype support artifact

## Draft Status

The first substantive draft based on this outline is now in `docs/framework-draft.md`.
