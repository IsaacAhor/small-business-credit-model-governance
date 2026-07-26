# Evidence Map

This map explains what repository artifacts support and what they do not prove.
It is intended to keep reviewer-facing claims disciplined and prevent
overclaiming from synthetic demonstrations.

| Artifact | What it supports | What it does not prove |
| --- | --- | --- |
| `README.md` | Project objective, scope, intended users, and repository orientation | External adoption, regulatory approval, or production deployment |
| `PROJECT_BRIEF.md` | Plain-language summary of the problem, contribution, limitations, and intended users | Independent validation or market acceptance |
| `docs/framework-draft.md` | Method design for governance, monitoring, documentation, and oversight | Peer-reviewed publication status or field adoption |
| `docs/adverse-action-reason-accuracy-method.md` | Method design for reason generation, mapping, QA, and evidence packaging under Regulation B section 1002.9 | Legal sufficiency of any actual notice or current lender compliance |
| `docs/adverse-action-public-data-limitations.md` | Public-data boundary for SBA, PPP, CRA, HMDA, and 1071 use | That public data proves small-business adverse-action reason accuracy |
| `docs/private-data-spec-adverse-action-reasons.md` | Field specification for a future private deidentified validation run | That private data has been obtained or reviewed |
| `docs/system-charter.md` | System purpose, intended users, core capabilities, and non-objectives | Production readiness or institution-specific compliance |
| `schemas/` | Structured data contracts for governed records and evidence-pack manifests | Completeness for every lender, model type, or legal requirement |
| `src/credit_gov/` | Implementation ability and reusable workflow logic | Production hardening, security review, or deployment at a lender |
| `data/synthetic/monthly-demo/` | Deterministic synthetic inputs for validation and monitoring demonstrations | Real applicant outcomes, real borrower data, or lender performance |
| `data/synthetic/adverse-action-reason-benchmark/` | Synthetic adverse-action reason benchmark inputs with controlled reason QA failures | Real small-business adverse-action notice accuracy, applicant data, or lender decision evidence |
| `examples/evidence-packs/` | Reviewer-ready example outputs generated from synthetic data, including monthly packs and the adverse-action reason benchmark | Legal compliance, fair-lending conclusions, real adverse-action notice accuracy, or production evidence |
| `tests/` | Technical discipline, regression coverage, and workflow reproducibility | Regulatory acceptance or independent audit approval |
| `.github/workflows/ci.yml` | Automated validation and test execution on repository changes | Substantive correctness of every governance judgment |
| `governance/` and `templates/` | Documentation standards, control structure, and reusable governance templates | Institution-specific policy approval or complete implementation |

## Claim Discipline

- Synthetic data should be described as demonstration data.
- Adverse-action reason benchmark outputs should be described as synthetic review
  triggers, not proof of real notice accuracy or compliance.
- HMDA should be described only as an off-domain reason-code mechanics proxy
  unless a future dataset supplies small-business decision drivers and notices.
- Fair-lending screening outputs should be described as review triggers, not
  legal conclusions.
- Evidence packs should be described as reviewer-ready examples, not production
  records.
- Tests should be described as reproducibility and regression checks, not
  certification.
- Public repository history can show execution and development discipline, but
  it does not by itself show external recognition or adoption.
