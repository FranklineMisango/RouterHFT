#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NS3_BUILD_DIR="${1:-${NS3_BUILD_DIR:-$HOME/ns-3.47/build}}"
NS3_ROOT="$(cd "$NS3_BUILD_DIR/.." && pwd)"
RESULTS_DIR="$ROOT_DIR/results"

if [[ ! -d "$NS3_BUILD_DIR" ]]; then
  echo "NS-3 build directory not found: $NS3_BUILD_DIR" >&2
  echo "Usage: $0 /absolute/path/to/ns-3.47/build" >&2
  exit 1
fi

"$ROOT_DIR/scripts/link_ns3_scratch.sh" "$NS3_BUILD_DIR"
mkdir -p "$RESULTS_DIR"

pushd "$NS3_ROOT" >/dev/null
"$NS3_ROOT/ns3" build
"$NS3_ROOT/ns3" run "scratch/RouterHFT/nic_router_pipeline --resultsDir=$RESULTS_DIR"
popd >/dev/null

echo "Simulation complete. CSV outputs in: $RESULTS_DIR"
echo "Plot with: python3 $ROOT_DIR/plot_results.py $RESULTS_DIR/latency.csv $RESULTS_DIR/throughput.csv"
