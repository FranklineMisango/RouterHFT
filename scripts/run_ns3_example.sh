#!/usr/bin/env bash
# Run RouterHFT NIC+Router hybrid NS-3 simulation.
# Usage: ./run_ns3_example.sh [/absolute/path/to/ns-3.47/build]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NS3_BUILD_DIR="${1:-${NS3_BUILD_DIR:-$HOME/ns-3.47/build}}"

if [[ ! -d "$NS3_BUILD_DIR" ]]; then
  echo "Set NS3_BUILD_DIR to your ns-3.47 build directory (or pass it as arg)" >&2
  exit 1
fi

"$ROOT_DIR/scripts/run_nic_router_hybrid.sh" "$NS3_BUILD_DIR"

echo "Done (check results/*.csv and plots)."
