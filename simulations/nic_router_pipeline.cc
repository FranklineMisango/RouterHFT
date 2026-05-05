#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"

#include <filesystem>
#include <fstream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("RouterHftNicRouterPipeline");

class HftTimestampHeader : public Header
{
public:
  HftTimestampHeader() = default;

  static TypeId GetTypeId()
  {
    static TypeId tid =
      TypeId("HftTimestampHeader").SetParent<Header>().AddConstructor<HftTimestampHeader>();
    return tid;
  }

  TypeId GetInstanceTypeId() const override
  {
    return GetTypeId();
  }

  void SetSequence(uint32_t sequence)
  {
    m_sequence = sequence;
  }

  void SetTxTimestampNs(uint64_t txTimestampNs)
  {
    m_txTimestampNs = txTimestampNs;
  }

  uint32_t GetSequence() const
  {
    return m_sequence;
  }

  uint64_t GetTxTimestampNs() const
  {
    return m_txTimestampNs;
  }

  uint32_t GetSerializedSize() const override
  {
    return sizeof(m_sequence) + sizeof(m_txTimestampNs);
  }

  void Serialize(Buffer::Iterator start) const override
  {
    start.WriteHtonU32(m_sequence);
    start.WriteHtonU64(m_txTimestampNs);
  }

  uint32_t Deserialize(Buffer::Iterator start) override
  {
    m_sequence = start.ReadNtohU32();
    m_txTimestampNs = start.ReadNtohU64();
    return GetSerializedSize();
  }

  void Print(std::ostream& os) const override
  {
    os << "seq=" << m_sequence << " txNs=" << m_txTimestampNs;
  }

private:
  uint32_t m_sequence = 0;
  uint64_t m_txTimestampNs = 0;
};

class HftSenderApp : public Application
{
public:
  HftSenderApp() = default;

  void Setup(Ipv4Address peerIpv4,
             uint16_t peerPort,
             uint32_t packetSize,
             uint32_t packetCount,
             Time interPacketGap)
  {
    m_peerIpv4 = peerIpv4;
    m_peerPort = peerPort;
    m_packetSize = packetSize;
    m_packetCount = packetCount;
    m_interPacketGap = interPacketGap;
  }

private:
  void StartApplication() override
  {
    m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
    m_socket->Connect(InetSocketAddress(m_peerIpv4, m_peerPort));
    SendPacket();
  }

  void StopApplication() override
  {
    if (m_sendEvent.IsPending())
    {
      Simulator::Cancel(m_sendEvent);
    }

    if (m_socket)
    {
      m_socket->Close();
      m_socket = nullptr;
    }
  }

  void SendPacket()
  {
    if (m_packetsSent >= m_packetCount)
    {
      return;
    }

    HftTimestampHeader header;
    header.SetSequence(m_packetsSent + 1);
    header.SetTxTimestampNs(static_cast<uint64_t>(Simulator::Now().GetNanoSeconds()));

    const uint32_t headerSize = header.GetSerializedSize();
    const uint32_t payloadSize = (m_packetSize > headerSize) ? (m_packetSize - headerSize) : 0;
    Ptr<Packet> packet = Create<Packet>(payloadSize);
    packet->AddHeader(header);

    m_socket->Send(packet);
    ++m_packetsSent;

    if (m_packetsSent < m_packetCount)
    {
      m_sendEvent = Simulator::Schedule(m_interPacketGap, &HftSenderApp::SendPacket, this);
    }
  }

  Ptr<Socket> m_socket;
  Ipv4Address m_peerIpv4;
  uint16_t m_peerPort = 0;
  uint32_t m_packetSize = 0;
  uint32_t m_packetCount = 0;
  Time m_interPacketGap = MicroSeconds(100);
  uint32_t m_packetsSent = 0;
  EventId m_sendEvent;
};

class HftReceiverApp : public Application
{
public:
  HftReceiverApp() = default;

  void Setup(uint16_t listenPort, const std::string& resultsDir)
  {
    m_listenPort = listenPort;
    m_resultsDir = resultsDir;
  }

private:
  void StartApplication() override
  {
    std::filesystem::create_directories(m_resultsDir);

    m_latencyCsv.open(m_resultsDir + "/latency.csv", std::ios::out | std::ios::trunc);
    m_throughputCsv.open(m_resultsDir + "/throughput.csv", std::ios::out | std::ios::trunc);

    m_latencyCsv << "sequence,tx_ns,rx_ns,latency_ns\n";
    m_throughputCsv << "second,packets_per_second,bits_per_second,bytes_received\n";

    m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
    m_socket->Bind(InetSocketAddress(Ipv4Address::GetAny(), m_listenPort));
    m_socket->SetRecvCallback(MakeCallback(&HftReceiverApp::HandleRead, this));

    m_throughputEvent = Simulator::Schedule(Seconds(1), &HftReceiverApp::ReportThroughput, this);
  }

  void StopApplication() override
  {
    if (m_throughputEvent.IsPending())
    {
      Simulator::Cancel(m_throughputEvent);
    }

    if (m_socket)
    {
      m_socket->Close();
      m_socket = nullptr;
    }

    if (m_latencyCsv.is_open())
    {
      m_latencyCsv.close();
    }

    if (m_throughputCsv.is_open())
    {
      m_throughputCsv.close();
    }
  }

  void HandleRead(Ptr<Socket> socket)
  {
    Address from;
    Ptr<Packet> packet;

    while ((packet = socket->RecvFrom(from)))
    {
      HftTimestampHeader header;
      if (packet->GetSize() < header.GetSerializedSize())
      {
        continue;
      }

      packet->RemoveHeader(header);

      const uint64_t rxNs = static_cast<uint64_t>(Simulator::Now().GetNanoSeconds());
      const uint64_t latencyNs = rxNs - header.GetTxTimestampNs();

      m_latencyCsv << header.GetSequence() << ',' << header.GetTxTimestampNs() << ',' << rxNs << ','
                   << latencyNs << '\n';

      ++m_totalPackets;
      m_totalBytes += packet->GetSize() + header.GetSerializedSize();
      ++m_packetsThisWindow;
      m_bytesThisWindow += packet->GetSize() + header.GetSerializedSize();
    }
  }

  void ReportThroughput()
  {
    const double bitsPerSecond = static_cast<double>(m_bytesThisWindow * 8);
    m_throughputCsv << m_currentSecond << ',' << m_packetsThisWindow << ',' << bitsPerSecond << ','
                    << m_totalBytes << '\n';

    m_packetsThisWindow = 0;
    m_bytesThisWindow = 0;
    ++m_currentSecond;

    m_throughputEvent = Simulator::Schedule(Seconds(1), &HftReceiverApp::ReportThroughput, this);
  }

  Ptr<Socket> m_socket;
  uint16_t m_listenPort = 0;
  std::string m_resultsDir;

  std::ofstream m_latencyCsv;
  std::ofstream m_throughputCsv;

  EventId m_throughputEvent;
  uint64_t m_totalPackets = 0;
  uint64_t m_totalBytes = 0;
  uint64_t m_packetsThisWindow = 0;
  uint64_t m_bytesThisWindow = 0;
  uint32_t m_currentSecond = 1;
};

int main(int argc, char* argv[])
{
  Time::SetResolution(Time::NS);

  std::string resultsDir = "results";
  std::string linkRate = "10Gbps";
  std::string linkDelay = "10us";
  uint32_t packetCount = 30000;
  uint32_t packetSize = 256;
  uint32_t intervalUs = 50;
  double simulationStopSeconds = 5.0;

  CommandLine cmd;
  cmd.AddValue("resultsDir", "Directory where latency.csv and throughput.csv are written", resultsDir);
  cmd.AddValue("linkRate", "Point-to-point link rate", linkRate);
  cmd.AddValue("linkDelay", "Point-to-point link delay", linkDelay);
  cmd.AddValue("packetCount", "Total number of packets to send", packetCount);
  cmd.AddValue("packetSize", "Packet size in bytes", packetSize);
  cmd.AddValue("intervalUs", "Inter-packet gap in microseconds", intervalUs);
  cmd.AddValue("simulationStopSeconds", "Simulation stop time in seconds", simulationStopSeconds);
  cmd.Parse(argc, argv);

  NodeContainer nodes;
  nodes.Create(3);

  PointToPointHelper p2p;
  p2p.SetDeviceAttribute("DataRate", StringValue(linkRate));
  p2p.SetChannelAttribute("Delay", StringValue(linkDelay));

  NetDeviceContainer nicToRouter = p2p.Install(nodes.Get(0), nodes.Get(1));
  NetDeviceContainer routerToConsumer = p2p.Install(nodes.Get(1), nodes.Get(2));

  InternetStackHelper internet;
  internet.Install(nodes);

  Ipv4AddressHelper ipv4;
  ipv4.SetBase("172.16.1.0", "255.255.255.0");
  ipv4.Assign(nicToRouter);
  ipv4.SetBase("172.16.2.0", "255.255.255.0");
  Ipv4InterfaceContainer consumerLink = ipv4.Assign(routerToConsumer);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  const uint16_t consumerPort = 9000;

  Ptr<HftReceiverApp> receiver = CreateObject<HftReceiverApp>();
  receiver->Setup(consumerPort, resultsDir);
  nodes.Get(2)->AddApplication(receiver);
  receiver->SetStartTime(Seconds(0.1));
  receiver->SetStopTime(Seconds(simulationStopSeconds));

  Ptr<HftSenderApp> sender = CreateObject<HftSenderApp>();
  sender->Setup(consumerLink.GetAddress(1),
                consumerPort,
                packetSize,
                packetCount,
                MicroSeconds(intervalUs));
  nodes.Get(0)->AddApplication(sender);
  sender->SetStartTime(Seconds(0.2));
  sender->SetStopTime(Seconds(simulationStopSeconds - 0.1));

  Simulator::Stop(Seconds(simulationStopSeconds));
  Simulator::Run();
  Simulator::Destroy();

  std::cout << "NIC -> Router -> Consumer simulation finished. Results in: " << resultsDir << std::endl;
  return 0;
}
