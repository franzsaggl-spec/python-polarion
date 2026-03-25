# v3 Release Checklist

## Pre-flight

- [ ] CI green on `main`
- [ ] `Release Readiness` workflow green
- [ ] Version in `pyproject.toml` is correct
- [ ] Changelog updated

## Functional confidence

- [ ] Contract tests pass (`pytest tests/`)
- [ ] Live integration smoke pass (`pytest tests/integration --run-integration -v`)
- [ ] Happy-path live flow pass (`tests/integration/test_v3_live_happy_path.py`)

## Packaging

- [ ] `python -m build`
- [ ] `twine check dist/*`

## Publish

- [ ] Create/verify release tag (`vX.Y.Z`)
- [ ] Publish GitHub release
- [ ] Confirm PyPI artifact visible

## Post-release

- [ ] Smoke install from PyPI in clean env
- [ ] Run minimal sample (`PolarionClient` + `projects.get`)
- [ ] Announce release notes
