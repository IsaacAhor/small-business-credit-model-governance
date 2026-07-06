# Framework Outline

## Working Title

Interpretable Model Governance and Fair-Lending Monitoring Framework for Machine-Learning-Based Small Business Credit Underwriting

## Purpose

This document outlines a practical framework for governing, monitoring, and documenting machine-learning-based small business credit underwriting systems in a way that improves transparency, explainability, fair-lending oversight, and model-risk management.

## Problem Statement

Small business credit underwriting increasingly relies on analytical systems that may be difficult to interpret, difficult to monitor, and difficult to justify when adverse decisions must be explained or when fairness concerns arise. A governance framework is needed to help institutions document decisions, monitor risk, assess explainability quality, and evaluate fair-lending concerns in a disciplined way.

## Target Users

- lender model-risk teams
- credit risk and analytics teams
- compliance and fair-lending functions
- internal audit and governance reviewers
- fintech teams building or monitoring underwriting systems

## Framework Objectives

- define core governance requirements for ML-based small business underwriting
- establish monitoring categories for fairness, drift, performance, and explanation quality
- support adverse action explanation design and review
- create a practical structure for less discriminatory alternative assessment
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

### 4. Explainability Controls

- explanation design principles
- reason-code mapping logic
- explanation stability and consistency review
- adverse action explanation considerations

### 5. Fair-Lending Monitoring

- segmentation logic
- disparity screening
- threshold governance
- less discriminatory alternative review triggers

### 6. Performance and Drift Monitoring

- model performance metrics
- population drift indicators
- feature drift indicators
- override and exception monitoring

### 7. Change Management

- version control
- retraining triggers
- model updates and approvals
- documentation refresh rules

### 8. Reporting and Escalation

- management reporting cadence
- issue logging
- remediation ownership
- board or committee escalation thresholds

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
