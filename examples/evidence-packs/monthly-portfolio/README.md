# Monthly Portfolio Evidence Pack

This folder contains a curated synthetic evidence pack generated from
`data/synthetic/monthly-portfolio/` (320 deterministic decisions).

It allows a reviewer to inspect the full workflow output at portfolio scale
without running the code, including the statistical additions documented in
`docs/fair-lending-statistics.md`. The files are demonstration-only artifacts
and do not contain real applicant, borrower, lender, or institution data.

## What This Pack Shows That The Minimal Demo Does Not

- Fair-lending screening findings that carry statistical significance blocks
  (test used, p-value, effect size, sample adequacy). One regional screen
  fires with significance; one segment screen fires without it — the contrast
  is deliberate and shows the screens distinguishing signal from noise.
- BISG proxy screening results (`bisg_proxy_results.json`), with
  probability-weighted group comparisons against a configured reference group.
- A less-discriminatory-alternative assessment
  (`lda_assessment_results.json`) comparing a baseline model to a supplied
  candidate on disparity and predictive separation.
- An adverse-action reason QA exception (`dec-0090`, missing reason code)
  that is generated deliberately by the dataset so reviewers can see how an
  exception becomes a tracked, owned issue.

## How To Review This Pack

1. Read `monitoring_report.md` for the plain-language summary.
2. Open `fair_lending_screening_results.json` for the screening findings with
   their significance blocks.
3. Open `bisg_proxy_results.json` for the proxy-weighted group comparisons.
4. Open `lda_assessment_results.json` for the baseline-versus-candidate
   assessment.
5. Open `reason_qa_results.json` for the reason QA exception and
   `issue_register.json` to see exceptions and breaches as tracked issues.
6. Open `reviewer_notes.md` and `reviewer_signoff.md` to see the human review
   step.

## Reproducing This Pack

The pack is deterministic. Regenerate it with:

```bash
python scripts/run_monthly_monitoring.py data/synthetic/monthly-portfolio --evidence-root evidence
```

Outputs are screening signals and governance review triggers, not legal
conclusions, compliance determinations, or evidence of production use.
