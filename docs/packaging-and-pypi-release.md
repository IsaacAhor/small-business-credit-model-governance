# Packaging And PyPI Release Guide

This guide documents how to build and publish the installable `credit-gov`
Python package from this repository.

The package distribution is a reproducibility and dissemination artifact. It
does not show production deployment, legal compliance, lender adoption,
regulatory approval, or independent validation by itself.

## Current Release Status

`v0.12.0` is the current release. Its assets are built and verified through the
controlled workflow described below. Do not reuse a prior release bundle as a
source for a later release.

TestPyPI and PyPI upload have not been performed. The steps below are the
controlled process for a future package-index upload.

## Package Shape

- Distribution name: `credit-gov`
- Import package: `credit_gov`
- Package metadata: `pyproject.toml`
- Source layout: `src/credit_gov/`
- Packaged schema resources: `src/credit_gov/schemas/json/`
- Packaged BISG reference resources: `src/credit_gov/reference/bisg/`
- Optional public-data commands: `credit-gov-sba-to-monitoring` and `credit-gov-make-sba-fixture`
- Formal governance command: `credit-gov-governance-review`
- Vendor oversight commands: `credit-gov-vendor-validate` and `credit-gov-vendor-report`

The root `schemas/` and `data/reference/bisg/` folders remain reviewer-facing
copies. `scripts/validate_repository.py` checks that those files stay synced
with the packaged resources.

## Local Build Check

Run from the repository root:

```bash
python -m pip install "pip==25.1.1" "build==1.5.0" "twine==6.2.0"
python -m build
python -m twine check dist/*
python scripts/validate_public_artifacts.py dist
```

The portability check inspects file content, filenames, and supported archive
member names and content. It reports unsafe member paths, absolute user-home
paths, email addresses, phone numbers, private-key markers, high-confidence
credential tokens, and Social Security number patterns. Findings use input and
member indexes so matched content and local paths are not echoed. Run it again
on every separately assembled verification archive before uploading release
assets:

The check fails closed for unreadable, encrypted, unsupported, binary,
oversized, or otherwise uninspected content. Such a finding is not a waiver:
inspect the source with an appropriate tool, create a reviewable derived
artifact, and scan that exact artifact again before distribution.

```bash
python scripts/validate_public_artifacts.py path/to/verification.zip
```

Publish derived run records with repository-relative paths. Preserve raw local
logs outside the release payload when they are needed for troubleshooting.

Create a checksum manifest for the exact artifacts and verify it from the
directory where the artifacts will be served:

```bash
(cd dist && sha256sum credit_gov-* > SHA256SUMS.txt)
(cd dist && sha256sum --check SHA256SUMS.txt)
python scripts/validate_public_artifacts.py dist/SHA256SUMS.txt
```

Then install the wheel into a clean environment and run smoke checks:

```bash
python -m pip install --force-reinstall dist/*.whl
credit-gov-validate data/synthetic/monthly-demo
credit-gov monitor data/synthetic/monthly-demo --evidence-root evidence
credit-gov change-review data/synthetic/monthly-portfolio
```

## Optional Public-Data Dependencies

The core package is stdlib-only. The SBA public-data adapter and synthetic SBA
fixture scripts require the optional public-data stack:

```bash
python -m pip install "credit-gov[public-data]"
```

For source-tree work before PyPI publication:

```bash
python -m pip install -e ".[public-data]"
credit-gov-make-sba-fixture --rows 4000 --out data/sba-7a-504-FIXTURE-synthetic.csv
credit-gov-sba-to-monitoring --input data/sba-7a-504-FIXTURE-synthetic.csv --program all
```

## TestPyPI Dry Run

Use TestPyPI before uploading to the real package index:

```bash
python -m twine upload --repository testpypi dist/*
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ credit-gov==0.12.0
```

Run the same installed-command smoke checks after the TestPyPI install.

## Controlled GitHub Release

GitHub releases are created only through the `Controlled release` workflow.
The workflow accepts an existing annotated semantic-version tag, checks that
the tag resolves to the checked-out commit and matches the package version,
runs the repository and unit checks, builds and scans the distributions,
creates SHA-256 checksums, and uploads a draft. It then downloads the draft,
verifies the checksums, scans the downloaded assets, publishes the draft, and
repeats the verification against the served assets.

The workflow uses the protected `release` environment. Keep a required manual
reviewer on that environment so a passing development build cannot publish a
release without a separate release decision.

If a run stops after draft creation, inspect the draft and its run logs. Do not
publish it manually or reuse its files; correct the source, delete the failed
draft through normal repository administration, and start a fresh run.

## PyPI Upload

Before uploading to PyPI:

1. Confirm the package name is still available or controlled by Isaac.
2. Confirm README, package metadata, release notes, and package contents have no
   non-public project or personal information.
3. Confirm CI has built and installed the wheel successfully.
4. Extract and validate every distribution and verification archive with
   `scripts/validate_public_artifacts.py`.
5. Resolve every unreadable or uninspected-content finding; skipped content is
   not cleared content.
6. Confirm the version number has not already been published.
7. Preserve the GitHub release, PyPI project page, wheel filename, hash, and
   upload timestamp in the project's release records.

Upload:

```bash
python -m twine upload dist/*
```

## Evidence-Care Language

Accurate claim:

> `credit-gov` was packaged as an installable Python distribution with
> versioned metadata, console entry points, packaged schemas/reference resources,
> CI build checks, and reproducible smoke tests.

Do not claim without independent proof:

- institutional adoption
- production deployment
- regulatory approval
- legal compliance certification
- field recognition
- real-world validation
- meaningful download demand
