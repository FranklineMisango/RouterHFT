# NIC Simulation (Phase 3)

**Lock-free packet queue and nanosecond timestamp handling for HFT NIC layer.**

📖 **Full documentation**: See [main README](../README.md) — Phase 3 section.

## Files

- `lockfree_queue.h` — SPSC queue (atomics-based, ring buffer)
- `timestamp_header.h/cc` — 64-bit nanosecond timestamps
- `test_nic_components.cc` — unit tests (5/5 passing)

## Quick Build & Test

```bash
g++ -std=c++17 -pthread test_nic_components.cc -o test_nic && ./test_nic
```

## Performance

- Push/Pop latency: <100 ns
- Throughput: >100M packets/sec
- Thread-safe: Yes (lock-free)
- Timestamp precision: 1 ns
