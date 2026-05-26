# Governance Control Matrix

Use this matrix to connect repository artifacts to the controls needed for
machine-learning-based small business credit underwriting.

| Control Area | Evidence Artifact | Review Question | Escalation Trigger |
| --- | --- | --- | --- |
| Model inventory | `governance/model-inventory-template.md` | Is the model purpose, owner, data status, and decision role clear? | Missing owner, use case, data provenance, or decision boundary |
| Validation | `governance/validation-checklist.md` | Has performance, explanation, fairness, and operational readiness been reviewed? | Material finding without reviewer, evidence, or remediation owner |
| Explainability | Framework and validation artifacts | Are explanations stable, reviewable, and tied to decision logic? | Reason-code drift, unexplained instability, or unmapped explanation changes |
| Fair-lending screening | `templates/fair-lending-monitoring-checklist.md` | Are segments, metrics, limitations, and review cadence defined? | Recurring disparity signal or undocumented comparison-group change |
| Adverse-action review | Inventory and validation artifacts | Is reason mapping documented and suitable for governance review? | Reason-code mapping changes without validation or reviewer approval |
| Change control | `governance/change-log-template.md` | Are material changes linked to impact, validation, and monitoring updates? | Feature, threshold, or reason-code changes without impact assessment |
| Data discipline | `governance/data-policy.md` | Is data synthetic, proxy, public, or production, and is provenance clear? | Data-like files without documented source and permitted use |
| Monitoring and escalation | Checklists, issues, and reports | Are threshold breaches assigned, dated, and tracked? | Breach without owner, decision, or follow-up date |
