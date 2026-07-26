# Packaging And PyPI Release Guide

This guide documents how to build and publish the installable `credit-gov`
Python package from this repository.

The package distribution is a reproducibility and dissemination artifact. It
does not show production deployment, legal compliance, lender adoption,
regulatory approval, or independent validation by itself.

## Package Shape

- Distribution name: `credit-gov`
- Import package: `credit_gov`
- Package metadata: `pyproject.toml`
- Source layout: `src/credit_gov/`
- Packaged schema resources: `src/credit_gov/schemas/json/`
- Packaged BISG reference resources: `src/credit_gov/reference/bisg/`
- Optional public-data commands: `credit-gov-sba-to-monitoring` and `credit-gov-make-sba-fixture`

The root `schemas/` and `data/reference/bisg/` folders remain reviewer-facing
copies. `scripts/validate_repository.py` checks that those files stay synced
with the packaged resources.

## Local Build Check

Run from the repository root:

```bash
python -m pip install --upgrade pip build twine
python -m build
python -m twine check dist/*
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
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ credit-gov==0.9.0
```

Run the same installed-command smoke checks after the TestPyPI install.

## PyPI Upload

Before uploading to PyPI:

1. Confirm the package name is still available or controlled by Isaac.
2. Confirm README, package metadata, release notes, and package contents have no
   private case-strategy language.
3. Confirm CI has built and installed the wheel successfully.
4. Confirm the version number has not already been published.
5. Preserve the GitHub release, PyPI project page, wheel filename, hash, and
   upload timestamp for the evidence index.

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