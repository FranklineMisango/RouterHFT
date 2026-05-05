// timestamp_queue.h
// Minimal placeholder for a timestamped packet queue.
// Replace with a lock-free implementation as needed (e.g., boost::lockfree or Folly).

#pragma once

#include <cstdint>
#include <vector>

struct TimestampedPacket {
  uint64_t timestamp_ns;
  std::vector<uint8_t> data;
};

class TimestampQueue {
public:
  TimestampQueue() {}
  void Push(const TimestampedPacket &p) { m_store.push_back(p); }
  bool Pop(TimestampedPacket &out)
  {
    if (m_store.empty()) return false;
    out = m_store.back();
    m_store.pop_back();
    return true;
  }

private:
  std::vector<TimestampedPacket> m_store;
};
