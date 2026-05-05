/*
 * udp_feed_handler.cc
 * NS-3 Application skeleton for a UDP feed handler with nanosecond timestamps.
 * Placeholders: timestamp injection, lock-free queue, congestion control hooks.
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/applications-module.h"

using namespace ns3;

class UDPFeedHandler : public Application
{
public:
  UDPFeedHandler() : m_socket(0), m_peer(), m_packetSize(512), m_interval(Seconds(0.000001)) {}
  virtual ~UDPFeedHandler() { m_socket = 0; }

  void Setup(Address peer, uint32_t packetSize, Time interval)
  {
    m_peer = peer;
    m_packetSize = packetSize;
    m_interval = interval;
  }

private:
  virtual void StartApplication() override
  {
    if (!m_socket)
    {
      m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
      m_socket->Connect(m_peer);
    }
    ScheduleTransmit();
  }

  virtual void StopApplication() override
  {
    if (m_socket)
    {
      m_socket->Close();
    }
    Simulator::Cancel(m_sendEvent);
  }

  void ScheduleTransmit()
  {
    m_sendEvent = Simulator::Schedule(m_interval, &UDPFeedHandler::SendPacket, this);
  }

  void SendPacket()
  {
    Ptr<Packet> packet = Create<Packet>(m_packetSize);

    // Example timestamp insertion point (nano-second precision)
    Time now = Simulator::Now();
    uint64_t ns = now.GetNanoSeconds();
    // TODO: attach ns to packet as metadata / custom header for downstream processing

    // TODO: push into lock-free dispatch queue here (placeholder)

    m_socket->Send(packet);

    // Re-schedule next transmit
    ScheduleTransmit();
  }

  Ptr<Socket> m_socket;
  Address m_peer;
  uint32_t m_packetSize;
  Time m_interval;
  EventId m_sendEvent;
};

int main(int argc, char *argv[])
{
  CommandLine cmd;
  cmd.Parse(argc, argv);

  // Simple 3-node pipeline: generator (node0) -> router (node1) -> consumer (node2)
  NodeContainer nodes;
  nodes.Create(3);

  PointToPointHelper p2p;
  p2p.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
  p2p.SetChannelAttribute("Delay", StringValue("100us"));

  NetDeviceContainer d0 = p2p.Install(nodes.Get(0), nodes.Get(1));
  NetDeviceContainer d1 = p2p.Install(nodes.Get(1), nodes.Get(2));

  InternetStackHelper internet;
  internet.Install(nodes);

  Ipv4AddressHelper ipv4;
  ipv4.SetBase("10.1.1.0", "255.255.255.0");
  ipv4.Assign(d0);
  ipv4.SetBase("10.1.2.0", "255.255.255.0");
  ipv4.Assign(d1);

  // Install UDPFeedHandler on node0 pointing to node2
  uint16_t port = 9000;
  Address sinkAddress(InetSocketAddress(Ipv4Address("10.1.2.2"), port));

  Ptr<UDPFeedHandler> feed = CreateObject<UDPFeedHandler>();
  nodes.Get(0)->AddApplication(feed);
  feed->Setup(sinkAddress, 256, MicroSeconds(100));
  feed->SetStartTime(Seconds(0.1));
  feed->SetStopTime(Seconds(2.0));

  // Simple sink on node2
  UdpServerHelper server(port);
  ApplicationContainer serverApp = server.Install(nodes.Get(2));
  serverApp.Start(Seconds(0.0));
  serverApp.Stop(Seconds(10.0));

  Simulator::Run();
  Simulator::Destroy();
  return 0;
}
