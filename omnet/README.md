# OMNeT++ Programmable NIC (Phase 4)

**Complete OMNeT++ simulation of a programmable NIC with timestamp injection and congestion control.**

📖 **Full documentation**: See [main README](../README.md) — Phase 4 section.

## Files

- `ProgrammableNIC.h/cc` — NIC module (packet ingestion, timestamping)
- `CongestionControl.h/cc` — ECN marking, queue management
- `TrafficGenerator.h/cc` — market data feed simulator
- `PacketSink.h/cc` — telemetry collector
- `HFT_NIC_Network.ned` — network topology
- `omnetpp.ini` — simulation configuration
- `Makefile` — build configuration

## Quick Build & Run

```bash
source ~/omnetpp-6.3.0-linux-x86_64/setenv
opp_makemake -f --deep -I.
make
./HFT_NIC_Network -u Cmdenv
```

## Performance

- NIC Ingestion: <1 µs per packet
- ECN Mark Threshold: 50–70% queue occupancy
- Drop Threshold: 90–95%
- Queue Capacity: 512–2048 packets
- Packets Tracked: Full statistics enabled

See [main README](../README.md) for full benchmarks.
