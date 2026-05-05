// examples/hft-nic-pipeline.cc
// Complete example: traffic generator -> NIC -> router -> sink
// Demonstrates full HFT pipeline with nanosecond timestamp tracking.
// Build: cp this to ns-3.47/scratch/ and run: ./waf --run scratch/hft-nic-pipeline

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("HFT_NIC_Pipeline");

int
main(int argc, char *argv[])
{
  Time::SetResolution(Time::NS);
  LogComponentEnable("HFT_NIC_Pipeline", LOG_LEVEL_INFO);
  LogComponentEnable("UdpSocketImpl", LOG_LEVEL_INFO);
  LogComponentEnable("UdpL4Protocol", LOG_LEVEL_INFO);

  // Create nodes: generator (0), router (1), consumer (2)
  NodeContainer nodes;
  nodes.Create(3);
  NS_LOG_INFO("Created 3 nodes for HFT NIC pipeline");

  // Point-to-point links
  PointToPointHelper p2p;
  p2p.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
  p2p.SetChannelAttribute("Delay", StringValue("10us"));

  NetDeviceContainer d01 = p2p.Install(nodes.Get(0), nodes.Get(1));
  NetDeviceContainer d12 = p2p.Install(nodes.Get(1), nodes.Get(2));

  // Internet stack
  InternetStackHelper internet;
  internet.Install(nodes);

  Ipv4AddressHelper ipv4;
  ipv4.SetBase("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer i01 = ipv4.Assign(d01);
  ipv4.SetBase("10.1.2.0", "255.255.255.0");
  Ipv4InterfaceContainer i12 = ipv4.Assign(d12);

  NS_LOG_INFO("Network setup complete: 10.1.1.0/24 and 10.1.2.0/24");

  // UDP sink on node 2
  uint16_t port = 9000;
  UdpServerHelper server(port);
  ApplicationContainer serverApp = server.Install(nodes.Get(2));
  serverApp.Start(Seconds(0.0));
  serverApp.Stop(Seconds(10.0));

  // UDP client on node 0 (simulates market feed)
  UdpClientHelper client(i12.GetAddress(1), port);
  client.SetAttribute("MaxPackets", UintegerValue(10000));
  client.SetAttribute("Interval", TimeValue(MicroSeconds(100))); // ~10Kpps
  client.SetAttribute("PacketSize", UintegerValue(256));

  ApplicationContainer clientApp = client.Install(nodes.Get(0));
  clientApp.Start(Seconds(1.0));
  clientApp.Stop(Seconds(9.0));

  NS_LOG_INFO("Applications configured");

  // Flow monitor for statistics
  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  Simulator::Stop(Seconds(10.0));
  Simulator::Run();

  // Print flow statistics
  monitor->CheckForLostPackets();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(
      flowmon.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  NS_LOG_INFO("Flow Statistics:");
  for (auto &flow : stats) {
    Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(flow.first);
    NS_LOG_INFO("Flow " << flow.first << " (" << t.sourceAddress << " -> "
                        << t.destinationAddress << ")");
    NS_LOG_INFO("  Tx Packets: " << flow.second.txPackets);
    NS_LOG_INFO("  Rx Packets: " << flow.second.rxPackets);
    NS_LOG_INFO("  Lost Packets: " << flow.second.lostPackets.size());
    NS_LOG_INFO("  Mean Delay: " << flow.second.delaySum.GetSeconds() / flow.second.rxPackets
                                 << "s");
  }

  Simulator::Destroy();
  return 0;
}
