// timestamp-header.cc
// Implementation of custom timestamp header for NS-3.

#include "timestamp-header.h"
#include "ns3/buffer.h"
#include "ns3/log.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE("TimestampHeader");
NS_OBJECT_ENSURE_REGISTERED(TimestampHeader);

TimestampHeader::TimestampHeader() : m_timestamp_ns(0)
{
  NS_LOG_FUNCTION(this);
}

TimestampHeader::~TimestampHeader()
{
  NS_LOG_FUNCTION(this);
}

void
TimestampHeader::SetTimestamp(uint64_t ns)
{
  NS_LOG_FUNCTION(this << ns);
  m_timestamp_ns = ns;
}

uint64_t
TimestampHeader::GetTimestamp(void) const
{
  return m_timestamp_ns;
}

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
  os << "TimestampHeader(timestamp=" << m_timestamp_ns << "ns)";
}

uint32_t
TimestampHeader::GetSerializedSize(void) const
{
  return sizeof(uint64_t);
}

void
TimestampHeader::Serialize(Buffer::Iterator start) const
{
  NS_LOG_FUNCTION(this);
  start.WriteHtonU64(m_timestamp_ns);
}

uint32_t
TimestampHeader::Deserialize(Buffer::Iterator start)
{
  NS_LOG_FUNCTION(this);
  m_timestamp_ns = start.ReadNtohU64();
  return GetSerializedSize();
}

} // namespace ns3
