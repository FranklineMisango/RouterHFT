#!/usr/bin/env bash
# Run example NS-3 experiments (note: requires ns-3 installation)

set -euo pipefail

NS3_ROOT=${NS3_ROOT:-$HOME/ns-3}

if [ ! -d "$NS3_ROOT" ]; then
  echo "Set NS3_ROOT to your ns-3 checkout (e.g. /home/user/ns-3)" >&2
  exit 1
fi

echo "Copying examples into ns-3 scratch and running..."
cp nic_sim/udp_feed_handler.cc "$NS3_ROOT"/scratch/
cp integration/nic_router_pipeline.cc "$NS3_ROOT"/scratch/

pushd "$NS3_ROOT" >/dev/null
./waf build
./waf --run scratch/udp_feed_handler || true
./waf --run scratch/nic_router_pipeline || true
popd >/dev/null

echo "Done (check ns-3 output)."
