# Contributing to qgis-layer-diff

Thanks for your interest in contributing!

## Getting started

1. Fork the repo and clone locally
2. Install dev deps: `pip install -e ".[dev]"` or `uv sync --group dev`
3. Create a branch: `git checkout -b feat/your-feature`
4. Make changes, add tests
5. Run: `ruff check . && pytest test/ -v`
6. Submit a PR

## Plugin conventions

- Plugin entry point is `plugin.py`, main UI in `diff_dock/` package
- Core logic in `core/` module, tests in `test/`
- QGIS plugins require GPL-2.0-or-later license
- Test with QGIS 3.34+ (LTR) and latest QGIS
- UI components go in `diff_dock/` submodules (postgis_dialog, layer_utils, result_layers)

## Testing

- Core logic tests run without QGIS installed (pure Python + shapely)
- UI tests require QGIS — not run in CI but should pass locally
- Aim for >70% coverage on core logic (enforced in CI)
- Run: `pytest test/ -v --cov=core`

## CI

GitHub Actions runs ruff and pytest on every PR. All must pass before merge.

## Pull request process

1. Keep PRs focused — one feature or fix per PR
2. Update the CHANGELOG if applicable
3. Ensure all CI checks pass
4. Request review from a maintainer

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
