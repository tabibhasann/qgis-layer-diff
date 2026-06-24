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

- Plugin entry point is `plugin.py`, main UI in `diff_dock.py`
- Core logic in `core/` module, tests in `test/`
- QGIS plugins require GPL-2.0-or-later license
- Test with QGIS 3.34+ (LTR) and latest QGIS

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
