/*
 * nic_router_pipeline.cc
 * Integration skeleton that demonstrates how the NIC application and router
 * would be wired together in an NS-3 experiment.
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"

using namespace ns3;

int main(int argc, char *argv[])
{
  CommandLine cmd;
  cmd.Parse(argc, argv);

  // This file is a high-level integration example. The real implementations
  // should move NIC logic into a reusable Application class (see nic_sim/).

  NodeContainer nodes;
  nodes.Create(3);

  PointToPointHelper p2p;
  p2p.SetDeviceAttribute("DataRate", StringValue("10Gbps"));
  p2p.SetChannelAttribute("Delay", StringValue("10us"));

  NetDeviceContainer dev0 = p2p.Install(nodes.Get(0), nodes.Get(1));
  NetDeviceContainer dev1 = p2p.Install(nodes.Get(1), nodes.Get(2));

  InternetStackHelper internet;
  internet.Install(nodes);

  Ipv4AddressHelper ipv4;
  ipv4.SetBase("172.16.1.0", "255.255.255.0");
  ipv4.Assign(dev0);
  ipv4.SetBase("172.16.2.0", "255.255.255.0");
  ipv4.Assign(dev1);

  // TODO: Install nic_sim::UDPFeedHandler on node0, router logic on node1,
  // and an application consumer on node2. Collect timestamp metadata at each hop.

  Simulator::Run();
  Simulator::Destroy();
  return 0;
}
