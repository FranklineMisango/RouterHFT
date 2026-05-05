// lockfree_queue.h
// Simple lock-free ring buffer queue using atomic operations.
// Suitable for producer-consumer packet dispatch in NIC simulation.

#pragma once

#include <atomic>
#include <cstdint>
#include <cstring>
#include <memory>
#include <vector>

struct Packet {
  uint64_t timestamp_ns;
  uint16_t length;
  uint8_t data[1024]; // Max packet size
};

class LockFreeQueue {
public:
  explicit LockFreeQueue(size_t capacity = 1024) : m_capacity(capacity)
  {
    m_buffer.resize(capacity);
    m_head.store(0, std::memory_order_relaxed);
    m_tail.store(0, std::memory_order_relaxed);
  }

  bool Push(const Packet &p)
  {
    size_t tail = m_tail.load(std::memory_order_acquire);
    size_t next_tail = (tail + 1) % m_capacity;
    if (next_tail == m_head.load(std::memory_order_acquire)) {
      return false; // queue full
    }
    m_buffer[tail] = p;
    m_tail.store(next_tail, std::memory_order_release);
    return true;
  }

  bool Pop(Packet &out)
  {
    size_t head = m_head.load(std::memory_order_acquire);
    if (head == m_tail.load(std::memory_order_acquire)) {
      return false; // queue empty
    }
    out = m_buffer[head];
    m_head.store((head + 1) % m_capacity, std::memory_order_release);
    return true;
  }

  size_t Size() const
  {
    size_t h = m_head.load(std::memory_order_acquire);
    size_t t = m_tail.load(std::memory_order_acquire);
    return (t >= h) ? (t - h) : (m_capacity - h + t);
  }

private:
  std::vector<Packet> m_buffer;
  std::atomic<size_t> m_head;
  std::atomic<size_t> m_tail;
  size_t m_capacity;
};
