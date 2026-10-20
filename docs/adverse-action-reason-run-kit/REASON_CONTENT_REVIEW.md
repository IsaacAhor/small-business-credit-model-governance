# Reason-content checks and operational authorization

Available in v0.13.0, contract `reason-content-review-v4`.
This gate checks recorded reasons, rendered reason segments for declined
decisions, and declared review records. It can export a checked review snapshot.
It never grants operational authorization, validates an entire notice or lending
model, or delivers a notice.

## Required behavior

Diagnostic generation and monitoring can complete successfully while their
outputs remain unauthorized for final use. Their command summaries explicitly
report `eligible_for_final_use: false` and `final_use_status: not_assessed`.
`generate-reasons --check` establishes regeneration equality only.

The separate export boundary recomputes validation and source-to-rendered-reason
checks from a captured input snapshot. It refuses export if:

- a required input or check is missing, malformed, not run, or not applicable;
- check results omit coverage, configuration or counts, or contradict their
  reported findings; a success label alone is insufficient;
- any reason QA finding remains, including unmapped or omitted principal
  drivers, inaccurate rendered text, or invalid mapping/template lifecycle;
- records are ambiguous, refer to non-declined decisions, or use a recognized
  credit-report-only placeholder;
- a declared failed decision component lacks adverse source evidence, a source
  reason is duplicated, or a used mapping omits its retirement status;
- required review is absent, incomplete, expired, future-dated, or bound to
  different input bytes, control sources, schemas, or a different gate version;
- review predates its recorded final decision, or a freshness check detects
  changed input or review state; or
- a declared material defect remains open, its materiality is unknown, or its
  claimed resolution lacks a captured evidence reference.

Every automated reason finding blocks export. There is no waiver flag or
override based on a declared review. Correct the inputs and reassess. A
resolved entry in the manual defect register cannot suppress an automated
finding. The batch passes only when every declined decision satisfies the
content and declared-review checks; no partial batch is exported.

## Machine-readable result

A passing assessment reports:

```json
{
  "gate_version": "reason-content-review-v4",
  "status": "reason_content_checks_passed",
  "reason_content_checks_passed": true,
  "operational_authorization_status": "not_provided",
  "authorized_for_operational_use": false,
  "eligible_for_final_use": false,
  "blockers": []
}
```

This is an abbreviated result; the full assessment includes scope, timestamps,
hashes, QA results, and required review checks. A pass means that the captured
records satisfy the automated controls and declared-review contract. It does
not authenticate the reviewer, establish evidence truth, or grant permission
to use the content in a live process.

A failed content assessment, including the assessment in a failed reviewed-snapshot
export, reports `status: blocked` and `reason_content_checks_passed: false`.
Operational authorization is always
`not_provided`, and both authorization Booleans above always remain false.
`eligible_for_final_use` is retained as a fail-closed field for older readers.
There is no successful `eligible`, `ready`, or `authorized` assessment status.

The export result's `ok` and `exported` fields describe local snapshot creation
only. Its authorization fields remain false. The artifact has
`artifact_type: reviewed_reason_content_snapshot`, explicit authorization fields,
and an `assessment` member using the contract above. The former `eligibility`
member is no longer emitted.

Diagnostic generation, monitoring, and benchmark acceptance are different
operations. Their results carry `purpose`, `final_use_status: not_assessed`,
and the same false authorization fields. These scope labels also appear in
newly generated pack manifests, reason-QA and rendered-notice-QA files, and benchmark
results. The standalone generation script and installed `generate-reasons`
command share the same implementation; write, equality-check, and drift results
all include a JSON `generation_summary` with that scope.

`verify-evidence` reports `purpose: evidence_pack_hash_verification_only`.
Its `ok: true` means the declared files match their recorded hashes. It does
not assess reason content, authenticate a reviewer, establish current approval,
or authorize use. Editing both a pack and its fingerprints can still pass that
check. Raw candidate arrays retain their input schema; they are not review
exports or authorization records.

Generated reviewer-signoff files are templates. Their reviewer status is copied
from the input manifest, labeled `input_manifest_unverified`, and does not
establish an authenticated signoff. Zero findings mean no escalation was
triggered by the checks that ran; missing or separate review requirements still
need assessment.

## Regulation and engineering choices

Authority checked on October 20, 2026:

- [12 CFR 1002.9(b)(2)](https://www.ecfr.gov/current/title-12/chapter-X/part-1002/subpart-A/section-1002.9)
  requires specific principal reasons. The
  [official interpretations of 9(b)(2)](https://www.consumerfinance.gov/rules-policy/regulations/1002/interp-9/)
  explain the relationship to factors actually considered or scored and the
  applicable decision process. Automated consistency alone cannot establish
  that relationship.
- [Section 1002.9(a)(2)-(3)](https://www.consumerfinance.gov/rules-policy/regulations/1002/9/)
  contains alternatives for providing reasons and distinct business-credit
  procedures. The gate does not assume that every transaction requires an
  initial written reason statement or apply a universal 30-day deadline.
- [Appendix C, paragraphs 3-5](https://www.consumerfinance.gov/rules-policy/regulations/1002/c/)
  permits adaptation of reason wording to actual factors. A missing dictionary
  mapping calls for an accurate supported correction, not substitution of a
  convenient mapped factor.

The law does not prescribe this software architecture. Blocking review export
when material reason defects remain unresolved is the project's conservative
engineering control; this package provides no operational authorization.
Review remains necessary for the actual selection method, principal
factor coverage, specificity, applicability, and timing. There is no universal
legal four-reason cap encoded in this gate. The configured synthetic rank limit
requires justification; reducing it does not establish that an omitted factor
is legally immaterial.

The declared review validity interval is an engineering check, not operational
approval or a calculation of a regulatory deadline. A block does not suspend notice duties.
The responsible process must handle escalation, timely lawful notification,
requests for reasons, and prompt correction separately. This reason-content
gate does not block a separately justified action notice or notice of the right
to request reasons.

The synthetic lifecycle check uses the decision timestamp. The lifecycle review
must address whether that convention fits the intended use and any separately
timed notice event. This implementation does not automatically determine
notice-event applicability or legal sufficiency.

## Local workflow

With the package installed from this working tree:

```text
credit-gov generate-reasons path/to/dataset
credit-gov assess-reason-content path/to/dataset
credit-gov export-reviewed-reasons path/to/dataset --output path/to/new-reviewed-reasons.json
```

Generation uses `reason-fidelity-policy.json`, `adverse-action-notice-template.json`,
and `reason-selection-methods.json` together when supplied. It then writes
source-to-notice reason records, including the controlled text, source ranks,
mapping, method, policy, and template identifiers. The configured principal rank
limit determines the maximum number of generated candidates. Partial, null, or
invalid configuration fails before replacing candidates, including blank or
wrongly typed identifiers, invalid template dates, and missing methods for
declined decision components. Basic diagnostic generation remains available
when all three files are absent and there are no source-component annotations,
rendered notices, or review records. A dataset with those richer inputs requires
all three configuration files and cannot silently downgrade to basic output.
Basic records cannot satisfy the content gate. The JSON summary identifies the
record mode. Generation is not a full dataset or reason-content assessment.

Generation does not create a review or replace rendered notices. Supply the
actual rendered reason segments separately, check them against the generated
records, and complete or renew review after the inputs are final. Generation
success does not establish that any defect has been resolved.

Assessment and review export return exit code 1 when blocked. Exit code 0 means content checks
passed or the reviewed snapshot was exported; it never means operational
authorization. Assessment writes JSON to standard output. Export writes only a
new local file outside the input dataset; it never overwrites an existing file
and has no delivery operation. An I/O failure also returns exit code 1.

Python callers use `assess_reason_content` and `export_reviewed_reasons` in
`credit_gov.reason_content`. The earlier local `credit_gov.final_use` module
and `assess-final-use` / `export-final-reasons` commands have been removed.
Those command names now fail as unknown commands with exit code 2 and create
no export. Migrate callers to the content-only API; a content pass does not
replace an operational permission check.

Keep review evidence as top-level JSON inputs in the dataset. Run assessment to
obtain `snapshot_sha256`. After substantive review, create `reason-content-review.json`
in the dataset. All top-level JSON inputs, including evidence, are bound by exact
byte hashes; the review file is excluded from its own binding and is hashed
separately. Any input byte change, even formatting, requires a renewed review.
Nested or external files are not captured evidence. JSON inputs must be regular
files; linked inputs are rejected. Evidence must contain a non-empty structured
record, not a null value or empty placeholder.

The binding also includes the control source files and effective validation
schemas, exposed as `control_sha256` in assessment output. Changes to those
files invalidate existing review bindings even if the gate version label is unchanged.
Version 4 rejects earlier review versions. A dataset containing the old
`final-use-review.json` is blocked, even if a new review file also exists.
Preserve the old record outside the active dataset, account for its defects,
and update any manifest reference to its retired filename. Then rerun assessment
and complete a fresh `reason-content-review.json`. A manifest reference to a
missing file remains a validation error; migration does not bypass that check.
Renaming an old review or copying its digest does not migrate it. Source changes
also invalidate its binding. Generation recognizes both filenames and case
variants as review inputs when checking for incomplete source-to-notice
configuration. Case variants of configuration and rendered-notice filenames
also prevent a silent fallback to basic mode on case-sensitive filesystems;
use the documented filenames for the full workflow.
All relevant events use the existing whole-second UTC timestamp contract.
Review may occur at or after its final decision, and its validity interval must
include the assessment/export time.

The required review contract is:

```json
{
  "gate_version": "reason-content-review-v4",
  "snapshot_sha256": "copy-the-current-assessment-digest",
  "reviewed_by": "responsible-reviewer-reference",
  "reviewed_at": "actual-review-time-in-YYYY-MM-DDTHH:MM:SSZ",
  "valid_until": "justified-expiry-in-YYYY-MM-DDTHH:MM:SSZ",
  "known_defects_complete": false,
  "material_defects": [],
  "decision_reviews": [
    {
      "decision_id": "dec-0002",
      "checks": {
        "actual_factors_and_principal_reasons": {
          "status": "not_assessed",
          "rationale": "Document the selection method, coverage, and actual decision factors.",
          "evidence_files": ["review-evidence.json"]
        },
        "specificity_and_accuracy": {
          "status": "not_assessed",
          "rationale": "Document the accuracy and specificity of each explanation.",
          "evidence_files": ["review-evidence.json"]
        },
        "notice_applicability_and_timing": {
          "status": "not_assessed",
          "rationale": "Document transaction category, procedure, relevant events and timing.",
          "evidence_files": ["review-evidence.json"]
        },
        "lifecycle_basis": {
          "status": "not_assessed",
          "rationale": "Document mapping and template applicability at the relevant events.",
          "evidence_files": ["review-evidence.json"]
        }
      }
    }
  ]
}
```

This template intentionally fails the content-review checks. Supply one review
per declined decision. Each check requires `status: satisfied`, a substantive rationale, and
at least one captured evidence filename. Set `known_defects_complete: true` only
after accounting for known defects. Each defect record must contain exactly
`defect_id`, Boolean `material`, `status` (`open` or `resolved`), `rationale`, and
`evidence_files`. A material resolved defect needs evidence supporting its
resolution. An open nonmaterial defect needs evidence supporting that
classification. Missing or unknown materiality blocks export.

Export assesses again, without accepting a cached passing report. It writes
the exact assessed reason outputs, rendered reason segments, review, and
assessment with hashes. Before returning a content pass or installing an export,
it compares the current input and review-record bytes and control hashes with the
assessed snapshot. Differences, missing files, or unreadable inputs detected at
that check block the operation. The complete review time interval is checked
again before export, including clock rollback that would make the review
future-dated. A failed reviewed-snapshot export returns a blocked assessment.
Existing exports remain historical
snapshots; a new assessment does not revoke, update, or validate previously
copied artifacts.
Earlier version 1 or version 2 exports may still contain the superseded
`eligible_for_final_use: true` field. They are not operational authorization and
are not rewritten or recalled by this change. Hash verification cannot upgrade
them to current authorization.

## Limits and integration

Review records are editable attestations, not authenticated signatures. The program
checks evidence presence and binding, not its substantive truth, reviewer
authority, or completeness of external defect disclosure. Passing means the
captured content and attestations satisfy these declared checks; it establishes
neither regulatory compliance, independent validation, nor deployment readiness.

A consuming application needs a separate operational authorization boundary
appropriate to its actual use and trust model, enforced on every relevant path.
A content-check pass, raw diagnostic file, review export, edited artifact, or
monitoring success is not that permission. This local package cannot prevent a
separate application or person from copying or using content. Production
integration would need appropriate access control, authenticated and authorized
review, current approval state, delivery controls, retention, and notice handling.

Keep the dataset, review and installed controls stable during an operation.
Freshness checks detect changes present at the checks; they are not a
transactional lock against an uncoordinated writer, a durable revocation ledger,
or protection against restoring an old set of files. A restored unexpired review
can pass the content checks again; a change after the last freshness check can
leave an export as an earlier checked snapshot. Neither case causes this program
to issue operational authorization. These are documented limits, not claims of replay
prevention or coordinated writes. A production consumer needs authoritative
approval state and coordination with its writers, and must check validity again
at actual use. A trusted local process and clock are
assumed. Hashing source files does not authenticate the running interpreter or
protect against in-process tampering.
Exported JSON is editable; its scope labels are not signatures or an enforcement
mechanism for a consuming application.

The deferred operational approval system would need authenticated reviewer
identities and role permissions, tamper-evident approvals bound to a specific
version and use, authoritative revocation and replay checks, and coordination
between dataset changes, approval state, and the consuming operation. None is
implemented by this content gate or by the diagnostic source fingerprints.

Change the gate version when changing its review contract or assessment
semantics. Source and schema hashes detect local file changes; they are not
signed executable attestations.
Tests in `tests/test_reason_content.py` demonstrate this bounded control with
synthetic cases; they do not establish real-world reason accuracy.
