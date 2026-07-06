# Evidence Map

This map explains what repository artifacts support and what they do not prove.
It is intended to keep reviewer-facing claims disciplined and prevent
overclaiming from synthetic demonstrations.

| Artifact | What it supports | What it does not prove |
| --- | --- | --- |
| `README.md` | Project objective, scope, intended users, and repository orientation | External adoption, regulatory approval, or production deployment |
| `PROJECT_BRIEF.md` | Plain-language summary of the problem, contribution, limitations, and intended users | Independent validation or market acceptance |
| `docs/framework-draft.md` | Method design for governance, monitoring, documentation, and oversight | Peer-reviewed publication status or field adoption |
| `docs/system-charter.md` | System purpose, intended users, core capabilities, and non-objectives | Production readiness or institution-specific compliance |
| `schemas/` | Structured data contracts for governed records and evidence-pack manifests | Completeness for every lender, model type, or legal requirement |
| `src/credit_gov/` | Implementation ability and reusable workflow logic | Production hardening, security review, or deployment at a lender |
| `data/synthetic/monthly-demo/` | Deterministic synthetic inputs for validation and monitoring demonstrations | Real applicant outcomes, real borrower data, or lender performance |
| `examples/evidence-packs/monthly-demo/` | Reviewer-ready example outputs generated from synthetic data | Legal compliance, fair-lending conclusions, or production evidence |
| `tests/` | Technical discipline, regression coverage, and workflow reproducibility | Regulatory acceptance or independent audit approval |
| `.github/workflows/ci.yml` | Automated validation and test execution on repository changes | Substantive correctness of every governance judgment |
| `governance/` and `templates/` | Documentation standards, control structure, and reusable governance templates | Institution-specific policy approval or complete implementation |

## Claim Discipline

- Synthetic data should be described as demonstration data.
- Fair-lending screening outputs should be described as review triggers, not
  legal conclusions.
- Evidence packs should be described as reviewer-ready examples, not production
  records.
- Tests should be described as reproducibility and regression checks, not
  certification.
- Public repository history can show execution and development discipline, but
  it does not by itself show external recognition or adoption.
