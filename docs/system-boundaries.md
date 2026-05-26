# System Boundaries

## In Scope

The system covers governance-support functions for machine-learning-based small business credit underwriting models, including:

- model record validation
- threshold-set validation
- monitoring metric computation
- reason-code QA support
- drift and disparity-oriented screening
- breach and issue record generation
- evidence-pack assembly

## Out of Scope

The system does not cover:

- live underwriting or production decision execution
- direct customer communication
- legal or regulatory conclusions
- portfolio strategy decisions outside the monitoring workflow
- institution-specific policy approval outside recorded signoff artifacts

## Boundary Distinctions

### Underwriting vs Governance

The system documents and evaluates governance evidence. It does not act as the production underwriting engine.

### Monitoring Inputs vs Source Systems

The system assumes that source-system data or derived monitoring records already exist in structured form. It validates and processes those records; it does not attempt to replace upstream data infrastructure.

### Screening vs Adjudication

Fair-lending or explanation QA outputs are screening and review artifacts. They are not final legal determinations.

### Evidence vs Adoption

Evidence packs show that a workflow can be executed and reviewed. They do not by themselves prove operational adoption by outside institutions.

## Data Boundary Expectations

The system should keep clear separation between:

- underwriting-relevant fields
- monitoring-only fields
- configuration records
- derived outputs
- reviewer commentary or signoff artifacts

## Synthetic Data Boundary

Early implementation may rely on synthetic data for demonstrations. When synthetic data is used:

- its synthetic status must be disclosed clearly
- limitations must be documented
- outputs must not be described as production performance or production fairness results

## Repository Boundary

The repository is a governance evidence engine, not a general-purpose ML platform. Additions should remain aligned to:

- model governance
- explainability review
- fair-lending monitoring
- documentation and evidence generation
- small business underwriting use cases
