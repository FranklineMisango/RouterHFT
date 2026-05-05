// TrafficGenerator.cc
// OMNeT++ traffic generator implementation.

#include "TrafficGenerator.h"

Define_Module(TrafficGenerator);

TrafficGenerator::TrafficGenerator()
{
  sendMsg = nullptr;
  packetsSent = 0;
}

TrafficGenerator::~TrafficGenerator()
{
  cancelAndDelete(sendMsg);
}

void
TrafficGenerator::initialize()
{
  numPackets = par("numPackets").intValue();
  interArrivalTime = par("interArrivalTime").doubleValue();
  packetSize = par("packetSize").intValue();
  packetsSent = 0;
  
  sendMsg = new cMessage("SendPacket");
  scheduleAt(interArrivalTime, sendMsg);
  
  EV << "TrafficGenerator started: numPackets=" << numPackets 
     << ", interArrival=" << interArrivalTime << "s, size=" << packetSize << "B\n";
}

void
TrafficGenerator::handleMessage(cMessage *msg)
{
  if (msg == sendMsg) {
    if (packetsSent < numPackets) {
      char name[40];
      sprintf(name, "Market-Data-%d", packetsSent);
      
      cPacket *pkt = new cPacket(name, 1);
      pkt->setByteLength(packetSize);
      pkt->setCreationTime(simTime());
      
      send(pkt, "out");
      packetsSent++;
      
      if (packetsSent < numPackets) {
        scheduleAt(simTime() + interArrivalTime, sendMsg);
      }
    }
  }
}

void
TrafficGenerator::finish()
{
  recordScalar("Total Packets Sent", packetsSent);
  EV << "TrafficGenerator finished: sent " << packetsSent << " packets\n";
}
