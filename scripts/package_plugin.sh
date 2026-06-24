#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
DIST_DIR="${DIST_DIR:-dist}"
BUILD_ROOT="${BUILD_ROOT:-build/qgis-plugin-ci}"
PLUGIN_DIR="${PLUGIN_DIR:-qgis_layer_diff}"
QGIS_PLUGIN_CI_BIN="${QGIS_PLUGIN_CI_BIN:-qgis-plugin-ci}"

if [[ -z "$VERSION" ]]; then
  VERSION="$(awk -F= '/^version=/{print $2; exit}' metadata.txt)"
fi

if [[ -z "$VERSION" ]]; then
  echo "Could not determine plugin version from metadata.txt" >&2
  exit 2
fi

if ! command -v "$QGIS_PLUGIN_CI_BIN" >/dev/null 2>&1; then
  echo "qgis-plugin-ci is not available. Install it with: python3 -m pip install qgis-plugin-ci" >&2
  exit 127
fi

stage_dir="$(BUILD_ROOT="$BUILD_ROOT" PLUGIN_DIR="$PLUGIN_DIR" bash scripts/prepare_qgis_plugin_ci.sh)"

(
  cd "$stage_dir"
  "$QGIS_PLUGIN_CI_BIN" package "$VERSION"
)

archive="$stage_dir/$PLUGIN_DIR.$VERSION.zip"
if [[ ! -f "$archive" ]]; then
  echo "Expected archive was not created: $archive" >&2
  exit 1
fi

mkdir -p "$DIST_DIR"
cp "$archive" "$DIST_DIR/"
echo "Plugin archive copied to $DIST_DIR/$(basename "$archive")"
