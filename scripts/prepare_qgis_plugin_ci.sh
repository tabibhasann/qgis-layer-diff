#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="${PLUGIN_DIR:-qgis_layer_diff}"
BUILD_ROOT="${BUILD_ROOT:-build/qgis-plugin-ci}"

case "$BUILD_ROOT" in
  ""|"/"|".")
    echo "Refusing unsafe BUILD_ROOT: '$BUILD_ROOT'" >&2
    exit 2
    ;;
esac

rm -rf "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT/$PLUGIN_DIR"

rsync -a --delete \
  --exclude='.DS_Store' \
  --exclude='.coverage' \
  --exclude='.git' \
  --exclude='.github' \
  --exclude='.gitignore' \
  --exclude='.pytest_cache' \
  --exclude='.ruff_cache' \
  --exclude='*.pyc' \
  --exclude='*.zip' \
  --exclude='__pycache__' \
  --exclude='build' \
  --exclude='dist' \
  --exclude='scripts' \
  --exclude='test' \
  ./ "$BUILD_ROOT/$PLUGIN_DIR/"

cat > "$BUILD_ROOT/.qgis-plugin-ci" <<YAML
plugin_path: $PLUGIN_DIR
github_organization_slug: tabibhasann
project_slug: qgis-layer-diff
changelog_path: $PLUGIN_DIR/CHANGELOG.md
changelog_include: true
YAML

cp CHANGELOG.md "$BUILD_ROOT/CHANGELOG.md"

git -C "$BUILD_ROOT" init -q
git -C "$BUILD_ROOT" config user.email "codex@example.com"
git -C "$BUILD_ROOT" config user.name "Codex"
git -C "$BUILD_ROOT" add .
git -C "$BUILD_ROOT" commit -q -m "Stage Layer Diff plugin for qgis-plugin-ci"

echo "$BUILD_ROOT"
