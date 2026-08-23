# Synthetic Vendor-Oversight Evidence Pack

This checked-in example is generated from the fictional
`baseline-complete` vendor-risk fixture and the synthetic monthly-demo model
context. It shows component inventory, decision authority, source-class and
applicability records, vendor-transparency limits, compensating controls,
heightened monitoring, business-credit notice controls, review gaps, and
reviewer signoff status.

Regenerate it from the repository root:

```bash
python scripts/build_vendor_risk_evidence_pack.py \
  data/synthetic/credit-union-vendor-risk/baseline-complete \
  data/synthetic/monthly-demo \
  examples/evidence-packs/credit-union-vendor-risk \
  --overwrite
```

The manifest hashes the five core-context inputs, six vendor-contract inputs,
every distinct supporting-evidence file referenced by the records, and three
substantive generated outputs. JSON inputs use a sorted, compact canonical form
and UTF-8 text inputs normalize line endings to LF so input hashes remain stable
across operating systems. Generated outputs are written with LF endings and
hashed byte-for-byte. `README.md` is explanatory documentation outside that
evidence set.

All named organizations, products, contracts, reviewers, and decisions are
synthetic. This evidence pack is not institutional adoption, independent
external validation, a legal opinion, a compliance certification, a finding of
model accuracy or notice legal sufficiency, or regulatory approval.
