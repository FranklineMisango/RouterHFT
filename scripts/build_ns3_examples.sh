#!/usr/bin/env bash
# build_ns3_examples.sh
# Configure and build NS-3.47 with examples/tests enabled.
# Usage: ./build_ns3_examples.sh [/absolute/path/to/ns-3.47/build]

set -euo pipefail

NS3_BUILD_DIR="${1:-${NS3_BUILD_DIR:-$HOME/ns-3.47/build}}"
NS3_ROOT="$(cd "$NS3_BUILD_DIR/.." && pwd)"

if [ ! -d "$NS3_ROOT" ] || [ ! -f "$NS3_ROOT/CMakeLists.txt" ]; then
  echo "Error: NS-3 root not found from build dir: $NS3_BUILD_DIR" >&2
  echo "Usage: $0 /absolute/path/to/ns-3.47/build" >&2
  exit 1
fi

echo "=== RouterHFT NS-3 Build ==="
echo "NS-3 Root: $NS3_ROOT"
echo "NS-3 Build Dir: $NS3_BUILD_DIR"

mkdir -p "$NS3_BUILD_DIR"
pushd "$NS3_BUILD_DIR" >/dev/null
cmake .. -GNinja -DNS3_EXAMPLES=ON -DNS3_TESTS=ON
ninja
popd >/dev/null

echo "✓ NS-3 configured and built"
echo "Next: ./scripts/run_nic_router_hybrid.sh $NS3_BUILD_DIR"
