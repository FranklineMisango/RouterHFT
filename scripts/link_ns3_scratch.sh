#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NS3_BUILD_DIR="${1:-${NS3_BUILD_DIR:-$HOME/ns-3.47/build}}"
NS3_SCRATCH_DIR="$(cd "$NS3_BUILD_DIR/.." && pwd)/scratch"
TARGET_LINK="$NS3_SCRATCH_DIR/RouterHFT"
SOURCE_DIR="$ROOT_DIR/simulations"

if [[ ! -d "$NS3_BUILD_DIR" ]]; then
  echo "NS-3 build directory not found: $NS3_BUILD_DIR" >&2
  echo "Usage: $0 /absolute/path/to/ns-3.47/build" >&2
  exit 1
fi

mkdir -p "$NS3_SCRATCH_DIR"

if [[ -L "$TARGET_LINK" || -e "$TARGET_LINK" ]]; then
  rm -rf "$TARGET_LINK"
fi

ln -s "$SOURCE_DIR" "$TARGET_LINK"

echo "Linked $SOURCE_DIR -> $TARGET_LINK"
