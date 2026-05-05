/*
 * ns3_router.cc
 * Simple NS-3 router simulation skeleton showing where routing protocols and
 * prioritization hooks would be added.
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

  // Create three nodes: left, router, right
  NodeContainer nodes;
  nodes.Create(3);

  PointToPointHelper p2p;
  p2p.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
  p2p.SetChannelAttribute("Delay", StringValue("50us"));

  NetDeviceContainer d0 = p2p.Install(nodes.Get(0), nodes.Get(1));
  NetDeviceContainer d1 = p2p.Install(nodes.Get(1), nodes.Get(2));

  InternetStackHelper internet;
  internet.Install(nodes);

  Ipv4AddressHelper ipv4;
  ipv4.SetBase("192.168.1.0", "255.255.255.0");
  ipv4.Assign(d0);
  ipv4.SetBase("192.168.2.0", "255.255.255.0");
  ipv4.Assign(d1);

  // TODO: integrate OSPF/BGP models or external emulation (GNS3/EVE-NG)
  // TODO: add packet prioritization hooks (queue disciplines / tc/prio)

  Simulator::Run();
  Simulator::Destroy();
  return 0;
}
