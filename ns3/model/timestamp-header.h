// timestamp-header.h
// Custom NS-3 packet header carrying nanosecond-precision timestamps.

#ifndef TIMESTAMP_HEADER_H
#define TIMESTAMP_HEADER_H

#include "ns3/header.h"
#include <cstdint>

namespace ns3 {

class TimestampHeader : public Header
{
public:
  TimestampHeader();
  virtual ~TimestampHeader();

  void SetTimestamp(uint64_t ns);
  uint64_t GetTimestamp(void) const;

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

#endif // TIMESTAMP_HEADER_H
