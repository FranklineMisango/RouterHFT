// timestamp_header.cc
// Implementation of custom timestamp header for NS-3 packets.

#include "timestamp_header.h"
#include "ns3/log.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE("TimestampHeader");
NS_OBJECT_ENSURE_REGISTERED(TimestampHeader);

TypeId
TimestampHeader::GetTypeId(void)
{
  static TypeId tid = TypeId("ns3::TimestampHeader")
    .SetParent<Header>()
    .SetGroupName("Internet")
    .AddConstructor<TimestampHeader>();
  return tid;
}

TypeId
TimestampHeader::GetInstanceTypeId(void) const
{
  return GetTypeId();
}

void
TimestampHeader::Print(std::ostream &os) const
{
  os << "timestamp=" << m_timestamp_ns << "ns";
}

uint32_t
TimestampHeader::GetSerializedSize(void) const
{
  return sizeof(uint64_t);
}

void
TimestampHeader::Serialize(Buffer::Iterator start) const
{
  start.WriteHtonU64(m_timestamp_ns);
}

uint32_t
TimestampHeader::Deserialize(Buffer::Iterator start)
{
  m_timestamp_ns = start.ReadNtohU64();
  return GetSerializedSize();
}

} // namespace ns3
