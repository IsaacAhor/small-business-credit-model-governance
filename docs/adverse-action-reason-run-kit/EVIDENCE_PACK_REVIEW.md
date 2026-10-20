# Evidence Pack Review

This file explains how to inspect the generated adverse-action reason benchmark
evidence pack without reading the implementation first.

Evidence-pack folder:

```text
examples/evidence-packs/adverse-action-reason-benchmark/
```

Regenerate it with:

```bash
python scripts/run_adverse_action_reason_benchmark.py --overwrite
```

## Review Order

1. `README.md`
   Confirms the pack is synthetic and gives the short review sequence.
2. `adverse_action_reason_benchmark_report.md`
   Plain-language benchmark summary.
3. `adverse_action_reason_benchmark_results.json`
   Machine-readable benchmark checks and seeded failure observations.
4. `reason_qa_results.json`
   Standard reason-QA output from the shared monitoring workflow.
5. `issue_register.json`
   Review issues opened by the evidence workflow.
6. `monitoring_report.md`
   Broader monitoring-report context from the shared workflow.
7. `manifest.json`
   Evidence-pack inventory and provenance metadata.
8. `input_fingerprints.json`
   Dataset JSON hashes with CRLF and CR normalized to LF, for checkout portability.
9. `reviewer_notes.md` and `reviewer_signoff.md`
   Reviewer-facing notes and signoff template outputs.
10. `execution_provenance.json`
    Source revision, checkout state, and exact source-file and input-byte fingerprints.

Dataset JSON is captured once before validation. Validation, monitoring, optional
analyses and the benchmark's supplemental checks use that captured content,
including which optional JSON files were absent. Later changes on disk do not
change the run's inputs or its recorded hashes. External BISG references are
captured when loaded, and their parsed content and hashes come from the same bytes.

`input_files_sha256` identifies exact bytes, without newline normalization, under
`dataset/<filename>` and `reference/bisg/<configuration-field>` identifiers.
The dataset inventory includes all top-level JSON files supplied, including
files unused by a particular analysis. Reference identifiers name each input's
role; their digests identify the actual content selected by the reference loader,
including packaged fallbacks. `input_snapshot_sha256` hashes this mapping as UTF-8
JSON with sorted keys and compact separators. Retain the matching inputs and
references for reproduction. Capture is sequential, not an atomic filesystem
transaction; it identifies what was read without asserting that all files came
from one coordinated revision or remain current.

New runs identify the code package rather than the dataset's enclosing repository.
`source_revision` is the code checkout's observed commit;
`source_tree_state` reports `clean`, `modified`, or `unavailable` at the initial
source capture. This is Git's checkout observation; writing output artifacts
can subsequently change it. It does not assert that every hashed file belongs
to that commit. A modified
checkout cannot be reproduced from that commit alone. An unpacked installation
or unavailable Git metadata reports `unavailable` rather than claiming a clean
revision. Environment revision claims and Git environment redirection are not
used as observed provenance.

`source_files_sha256` records exact bytes under relative identifiers for package
Python files, packaged JSON resources, effective schemas (including overrides
without a packaged counterpart), and the benchmark driver when supplied.
`source_snapshot_sha256` is SHA-256 of that file-hash mapping serialized
as UTF-8 JSON with sorted keys and compact separators. Retain the matching source
files as well as inputs to reproduce a modified run; a digest cannot reconstruct
them. The software version is a package label, not a unique source identifier.

Source fingerprints are captured before dataset validation and analysis. File
hashes, aggregate identity, fingerprint format, scope and observed commit are
compared again before installing the monitoring pack and the benchmark pack.
A detected change fails the run. Benchmark output is staged until these checks
pass, so a source-check failure leaves an existing destination intact.
The copied monitoring pack must pass its existing integrity check before the
benchmark adds files or updates fingerprints. The completed staged pack is
checked again before installation. This prevents detected artifact changes from
being silently accepted as new benchmark output; it is not an authentication
check against a writer who edits both artifacts and their hash records.
Failed benchmark acceptance also returns failure without installing the pack.
Destinations that would replace the input dataset or its ancestors, or overlap
the source directories, are rejected before generation.
On replacement, the previous pack is moved to a sibling backup until the new pack
is installed. An installation failure restores the previous pack. If restoration
also fails, the error identifies the retained backup for manual recovery; temporary
staging cleanup does not delete it. Backup or staging cleanup failures are logged
as warnings; they do not change installation status or mask an earlier recovery
error. A reported leftover staging directory may require manual cleanup.
These safeguards handle filesystem exceptions;
they do not provide crash durability or coordinate concurrent writers. Use a
single writer or distinct output directories.
Keep the code and resources stable throughout execution, and start a fresh
process after editing source files.
This detects disk changes at the checks; it does not attest loaded bytecode,
authenticate an approval, or coordinate concurrent writers. Input and output
fingerprints remain separate from these source fingerprints. Older packs are
historical artifacts and do not gain source identification merely by passing
`verify-evidence`.

## What To Look For

Confirm that:

- the pack states that it is synthetic
- the benchmark result says expected seeded failures were observed
- reason-QA exceptions are traceable to specific applications and reason
  outputs
- source-to-rendered-notice traceability and reconciliation reports distinguish
  the final decision
  component, source driver, mapping, recorded reason text, visible notice
  segment, template, policy, and method versions
- reason-code mapping problems are separated from generic monitoring metrics
- the pack does not claim legal compliance, deployment, adoption, or external
  validation
- input fingerprints and manifest files exist for reproducibility
- generated manifests, QA outputs, and benchmark results explicitly report that
  operational authorization is not provided

Benchmark acceptance means expected seeded failure detection. It does not mean
the defective reason set passed the separate content-review gate.
`verify-evidence` success establishes matching files and hashes only; it does not
authenticate a reviewer or establish content accuracy or current approval.
The reviewer-signoff file is an unverified template, including any reviewer
status copied from inputs. A zero-finding result is not a completed review.
See [the result contract](REASON_CONTENT_REVIEW.md) for the separate local content workflow.

Legacy programmatic identifiers containing `fidelity` are compatibility labels
with the narrow meaning documented in `TERMINOLOGY.md`; they are not claims of a
unique model explanation, causal truth, actionability, or recourse.

## How To Read Failures

Failures are intentional when they match seeded benchmark conditions. They show
that the workflow can detect missing, stale, unmapped, generic, mismatched, or
out-of-scope reasons.

Unexpected failures should be treated as implementation issues and investigated
before citing the run.

## Citation Discipline

Use the evidence pack as proof of a reproducible synthetic method and reviewer-
ready packaging. Do not use it as proof of real small-business notice accuracy
or Regulation B compliance.
