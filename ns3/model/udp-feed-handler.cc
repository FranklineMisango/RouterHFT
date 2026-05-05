// udp-feed-handler.cc
// NS-3 implementation of UDP feed handler with nanosecond timestamp injection.

#include "udp-feed-handler.h"
#include "timestamp-header.h"
#include "ns3/socket.h"
#include "ns3/socket-factory.h"
#include "ns3/udp-socket-factory.h"
#include "ns3/packet.h"
#include "ns3/simulator.h"
#include "ns3/log.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE("UDPFeedHandler");
NS_OBJECT_ENSURE_REGISTERED(UDPFeedHandler);

TypeId
UDPFeedHandler::GetTypeId(void)
{
  static TypeId tid = TypeId("ns3::UDPFeedHandler")
    .SetParent<Application>()
    .SetGroupName("Applications")
    .AddConstructor<UDPFeedHandler>()
    .AddAttribute("RemoteAddress", "The destination Address of the outbound packets",
                  AddressValue(),
                  MakeAddressAccessor(&UDPFeedHandler::m_peer),
                  MakeAddressChecker())
    .AddAttribute("RemotePort", "The destination port of the outbound packets",
                  UintegerValue(9),
                  MakeUintegerAccessor(&UDPFeedHandler::m_peer),
                  MakeUintegerChecker<uint16_t>())
    .AddAttribute("PacketSize", "Size of echo packets (bytes)",
                  UintegerValue(1024),
                  MakeUintegerAccessor(&UDPFeedHandler::m_packetSize),
                  MakeUintegerChecker<uint32_t>())
    .AddAttribute("InterPacketGap", "Time between packet transmissions",
                  TimeValue(MilliSeconds(1)),
                  MakeTimeAccessor(&UDPFeedHandler::m_interPacketGap),
                  MakeTimeChecker());
  return tid;
}

UDPFeedHandler::UDPFeedHandler()
  : m_socket(0),
    m_packetSize(1024),
    m_dataRate(0),
    m_interPacketGap(MilliSeconds(1)),
    m_running(false),
    m_packetCount(0)
{
  NS_LOG_FUNCTION(this);
}

UDPFeedHandler::~UDPFeedHandler()
{
  NS_LOG_FUNCTION(this);
  m_socket = 0;
}

void
UDPFeedHandler::Setup(Address address, uint16_t port, uint32_t packetSize, Time interPacketGap)
{
  m_peer = InetSocketAddress(address, port);
  m_packetSize = packetSize;
  m_interPacketGap = interPacketGap;
}

void
UDPFeedHandler::StartApplication(void)
{
  NS_LOG_FUNCTION(this);

  if (!m_socket) {
    m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
    if (Ipv4Address::IsMatchingType(m_peer)) {
      m_socket->Bind();
    }
    m_socket->Connect(m_peer);
  }

  m_running = true;
  m_packetCount = 0;
  ScheduleTransmit(Seconds(0.0));
}

void
UDPFeedHandler::StopApplication(void)
{
  NS_LOG_FUNCTION(this);
  m_running = false;

  if (m_socket != 0) {
    m_socket->Close();
  }

  Simulator::Cancel(m_sendEvent);
}

void
UDPFeedHandler::ScheduleTransmit(Time dt)
{
  NS_LOG_FUNCTION(this << dt);
  if (m_running) {
    m_sendEvent = Simulator::Schedule(dt, &UDPFeedHandler::SendPacket, this);
  }
}

void
UDPFeedHandler::SendPacket(void)
{
  NS_LOG_FUNCTION(this);

  Ptr<Packet> p = Create<Packet>(m_packetSize);
  TimestampHeader tsh;
  tsh.SetTimestamp(GetNanosecondTimestamp());
  p->AddHeader(tsh);

  m_socket->Send(p);
  m_packetCount++;

  NS_LOG_INFO("Sent UDP feed packet #" << m_packetCount
              << " with timestamp=" << tsh.GetTimestamp() << "ns");

  m_txTrace(p);
  ScheduleTransmit(m_interPacketGap);
}

uint64_t
UDPFeedHandler::GetNanosecondTimestamp(void)
{
  Time now = Simulator::Now();
  return now.GetNanoSeconds();
}

} // namespace ns3
