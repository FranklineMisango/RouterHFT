// timestamp_header.h
// Custom packet header for carrying nanosecond-precision timestamps in NS-3 packets.

#pragma once

#include "ns3/header.h"
#include <cstdint>

namespace ns3 {

class TimestampHeader : public Header
{
public:
  TimestampHeader() : m_timestamp_ns(0) {}
  virtual ~TimestampHeader() {}

  void SetTimestamp(uint64_t ns) { m_timestamp_ns = ns; }
  uint64_t GetTimestamp() const { return m_timestamp_ns; }

  static TypeId GetTypeId(void);
  virtual TypeId GetInstanceTypeId(void) const;
  virtual void Print(std::ostream &os) const;
  virtual uint32_t GetSerializedSize(void) const;
  virtual void Serialize(Buffer::Iterator start) const;
  virtual uint32_t Deserialize(Buffer::Iterator start);

private:
  uint64_t m_timestamp_ns;
};

} // namespace ns3
