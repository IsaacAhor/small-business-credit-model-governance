# Contributing

## Purpose

This repository should accumulate traceable governance artifacts, not ad hoc notes.

Every material change should leave enough context for a reviewer to understand:

- what problem is being addressed
- what files or controls changed
- whether the change affects model behavior, governance, validation, or monitoring

## Contribution Rules

- Keep changes scoped. Do not mix governance-policy edits with unrelated
  formatting churn.
- Prefer additive history. Add new templates, records, or sections
  instead of overwriting evidence without explanation.
- Use explicit filenames. Prefer names that indicate purpose rather than
  temporary working labels.
- When introducing implementation assets later, place them in clearly
  named top-level directories and update the root README.

## Commit Guidance

Prefer commit messages that explain intent, for example:

- `docs: expand governance repository overview`
- `governance: add model inventory template`
- `ci: add markdown validation workflow`

## Pull Request Expectations

Each PR should state:

- the problem being solved
- the files or controls affected
- any follow-up work still required
- whether validation, approval, or monitoring procedures are impacted

Use the PR template in
`.github/pull_request_template.md`.

## Review Checklist

Before requesting review, confirm:

- the change is understandable without private context
- file and folder names are durable
- governance implications are called out directly
- follow-up work is tracked rather than implied
