# Synthetic Credit-Union Vendor-Risk Fixtures

These fixtures exercise the executable vendor-model oversight contracts without
using real member, applicant, credit-union, vendor, contract, incident, or
confidential model data. They reuse `data/synthetic/monthly-demo/` as the
validated core model/version/decision/reason context.
The matrix includes both valid and intentionally invalid cases so success and
failure behavior remain reviewable.

| Fixture | Expected result | Purpose |
| --- | --- | --- |
| `baseline-complete` | valid | Linked review, two components, a partial-transparency limitation, heightened monitoring, and a business-credit notice control. |
| `opaque-component` | valid | Unavailable model detail with a recorded limitation, compensating control, and residual-risk decision. |
| `material-change` | valid | Material model change with notice, assessment, and in-progress remediation. |
| `incident-escalation` | valid | Fictional security event with institution assessment and no reportability conclusion. |
| `notice-control-gap` | valid with reported gap | Pending notice-control disposition and conditional applicability review. |
| `invalid-missing-evidence` | invalid | Review record points to a missing evidence file. |
| `invalid-broken-link` | invalid | Component points to an unknown review. |

Validate the baseline fixture:

```bash
python scripts/validate_vendor_risk_run_kit.py \
  data/synthetic/credit-union-vendor-risk/baseline-complete \
  data/synthetic/monthly-demo
```

The records demonstrate data contracts and review-gap handling. They do not
establish institutional adoption, model accuracy, notice legal sufficiency,
compliance, safety, soundness, security, reliability, or regulatory approval.
