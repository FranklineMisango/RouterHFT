// PacketSink.cc
// OMNeT++ packet sink implementation.

#include "PacketSink.h"

Define_Module(PacketSink);

PacketSink::PacketSink()
{
  packetsReceived = 0;
  totalBytesReceived = 0;
}

PacketSink::~PacketSink()
{
}

void
PacketSink::initialize()
{
  packetsReceived = 0;
  totalBytesReceived = 0;
  EV << "PacketSink initialized\n";
}

void
PacketSink::handleMessage(cMessage *msg)
{
  cPacket *pkt = check_and_cast<cPacket*>(msg);
  
  packetsReceived++;
  totalBytesReceived += pkt->getByteLength();
  
  simtime_t latency = simTime() - pkt->getCreationTime();
  
  EV << "Packet received: " << pkt->getName() 
     << " size=" << pkt->getByteLength() << "B"
     << " latency=" << latency.str() << "\n";
  
  delete pkt;
}

void
PacketSink::finish()
{
  recordScalar("Packets Received", packetsReceived);
  recordScalar("Total Bytes Received", totalBytesReceived);
  
  EV << "PacketSink finished: received=" << packetsReceived 
     << " packets, " << totalBytesReceived << " bytes\n";
}
