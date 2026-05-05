#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_BIN="$ROOT_DIR/hft_smoke_test"
SRC_FILE="$ROOT_DIR/tests/cpp/hft_smoke_test.cpp"

c++ -std=c++17 -O2 -pthread "$SRC_FILE" -o "$OUT_BIN"
"$OUT_BIN"
