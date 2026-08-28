# Adverse-Action Reason Terminology

## Traceability And Reconciliation

In this repository, source-to-notice traceability and reconciliation means that
a recorded reason and rendered notice segment can be reconciled to the declared
decision component, source driver, selection convention, mapping, policy, and
template version.

The legacy programmatic key `source_to_notice_fidelity`, the
`credit_gov.reason_fidelity` module, `ReasonFidelityContext`, and related
compatibility identifiers are retained so existing datasets, commands, imports,
and reviewer artifacts continue to work. In current prose, `fidelity` in those
identifiers means only the record-level traceability and reconciliation defined
above.

This control does not establish:

- a unique or privileged explanation of a model prediction;
- causal truth or faithfulness under every explanation convention;
- applicant actionability or recourse;
- legal sufficiency or regulatory compliance; or
- production validation, institutional adoption, or effectiveness.

## Three Separate Review Questions

The run kit keeps three questions distinct:

1. **Convention traceability and reconciliation:** Did the recorded reason and
   notice segment follow the declared, versioned decision, selection, mapping,
   policy, and template records?
2. **Explanation-method faithfulness:** Does an explanation represent model
   behavior under a defined method, reference population, and set of
   assumptions?
3. **Recourse assessment:** Does an evaluated intervention reach a target model
   prediction under a declared, versioned action set and bounded method?

The current adverse-action reason controls answer the first question. They do
not answer the second or third by implication.
