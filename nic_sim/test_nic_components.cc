// test_nic_components.cc
// Unit tests for lock-free queue and timestamp handling.
// Compile with: g++ -std=c++11 -pthread test_nic_components.cc -o test_nic

#include "lockfree_queue.h"
#include <iostream>
#include <cassert>
#include <thread>
#include <chrono>

void test_lockfree_queue_basic()
{
  std::cout << "Test: LockFreeQueue basic push/pop... ";
  LockFreeQueue q(16);

  Packet p1;
  p1.timestamp_ns = 1000000;
  p1.length = 64;
  p1.data[0] = 0xAA;

  assert(q.Push(p1));
  assert(q.Size() == 1);

  Packet p_out;
  assert(q.Pop(p_out));
  assert(p_out.timestamp_ns == 1000000);
  assert(p_out.data[0] == 0xAA);
  assert(q.Size() == 0);

  std::cout << "PASS\n";
}

void test_lockfree_queue_full()
{
  std::cout << "Test: LockFreeQueue overflow... ";
  LockFreeQueue q(3); // capacity 3 holds 2 items (1 reserved as empty marker)

  Packet p;
  p.timestamp_ns = 0;
  p.length = 0;

  assert(q.Push(p));
  assert(q.Push(p));
  // Queue is now full (next push would overflow)
  assert(!q.Push(p));

  std::cout << "PASS\n";
}

void test_lockfree_queue_empty()
{
  std::cout << "Test: LockFreeQueue underflow... ";
  LockFreeQueue q(4);

  Packet p;
  assert(!q.Pop(p)); // pop from empty

  std::cout << "PASS\n";
}

void producer_task(LockFreeQueue &q, int count)
{
  for (int i = 0; i < count; i++) {
    Packet p;
    p.timestamp_ns = 1000000000ULL + i;
    p.length = 64 + (i % 256);
    p.data[0] = (uint8_t)(i & 0xFF);
    q.Push(p);
    std::this_thread::sleep_for(std::chrono::microseconds(10));
  }
}

void consumer_task(LockFreeQueue &q, int &consumed)
{
  Packet p;
  consumed = 0;
  while (consumed < 100) {
    if (q.Pop(p)) {
      consumed++;
    }
    std::this_thread::sleep_for(std::chrono::microseconds(5));
  }
}

void test_lockfree_queue_concurrent()
{
  std::cout << "Test: LockFreeQueue concurrent producer/consumer... ";
  LockFreeQueue q(128);

  int consumed = 0;
  std::thread prod(producer_task, std::ref(q), 100);
  std::thread cons(consumer_task, std::ref(q), std::ref(consumed));

  prod.join();
  cons.join();

  assert(consumed >= 100);
  std::cout << "PASS (consumed " << consumed << " packets)\n";
}

void test_timestamp_precision()
{
  std::cout << "Test: Timestamp nanosecond precision... ";
  Packet p1, p2;
  p1.timestamp_ns = 1234567890123456789ULL;
  p2.timestamp_ns = 9876543210987654321ULL;

  assert(p1.timestamp_ns == 1234567890123456789ULL);
  assert(p2.timestamp_ns == 9876543210987654321ULL);
  assert(p2.timestamp_ns - p1.timestamp_ns == 8641975320864197532ULL);

  std::cout << "PASS\n";
}

int main()
{
  std::cout << "\n=== NIC Component Unit Tests ===\n\n";

  try {
    test_lockfree_queue_basic();
    test_lockfree_queue_full();
    test_lockfree_queue_empty();
    test_lockfree_queue_concurrent();
    test_timestamp_precision();

    std::cout << "\n✓ All tests passed!\n\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "✗ Test failed: " << e.what() << "\n";
    return 1;
  }
}
