#!/usr/bin/env bash
# build_ns3_examples.sh
# Quick build script for NS-3 HFT examples
# Usage: ./build_ns3_examples.sh

set -euo pipefail

NS3_ROOT="${NS3_ROOT:-$HOME/ns-3.47}"
ROUTERHFT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$NS3_ROOT" ]; then
  echo "Error: NS3_ROOT=$NS3_ROOT not found" >&2
  echo "Set NS3_ROOT environment variable to your ns-3 installation" >&2
  exit 1
fi

echo "=== RouterHFT NS-3 Build ==="
echo "NS-3 Root: $NS3_ROOT"
echo "RouterHFT Dir: $ROUTERHFT_DIR"

# Copy example to NS-3 scratch
echo "Copying example to NS-3..."
mkdir -p "$NS3_ROOT/scratch"
cp "$ROUTERHFT_DIR/examples/hft-nic-pipeline.cc" "$NS3_ROOT/scratch/" || true

# Build NS-3
echo "Building NS-3..."
cd "$NS3_ROOT"
if [ ! -f wscript ]; then
  echo "Error: not in NS-3 root" >&2
  exit 1
fi

./waf clean >/dev/null 2>&1 || true
./waf configure --enable-examples --quiet
./waf build --quiet

echo "✓ NS-3 built successfully"

# Run example
echo "Running HFT NIC pipeline example..."
./waf --run "scratch/hft-nic-pipeline" --command-template="%s"

echo "✓ Example completed"
