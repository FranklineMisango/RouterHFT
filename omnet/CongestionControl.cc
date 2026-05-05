// CongestionControl.cc
// OMNeT++ implementation of congestion control with ECN marking and queue management.

#include "CongestionControl.h"

Define_Module(CongestionControl);

CongestionControl::CongestionControl()
{
  currentQueueLength = 0;
  droppedPackets = 0;
  ecnMarkedPackets = 0;
}

CongestionControl::~CongestionControl()
{
}

void
CongestionControl::initialize()
{
  maxQueueLength = par("maxQueueLength").intValue();
  dropThreshold = par("dropThreshold").doubleValue();
  ecnThreshold = par("ecnThreshold").doubleValue();
  currentQueueLength = 0;
  droppedPackets = 0;
  ecnMarkedPackets = 0;
  
  queueLengthVector.setName("Queue_Length");
  
  EV << "CongestionControl initialized: max=" << maxQueueLength 
     << ", drop_threshold=" << dropThreshold 
     << ", ecn_threshold=" << ecnThreshold << "\n";
}

void
CongestionControl::handleMessage(cMessage *msg)
{
  cPacket *pkt = check_and_cast<cPacket*>(msg);
  
  // Check ECN marking threshold
  if (shouldMarkECN()) {
    EV << "ECN marking packet " << pkt->getName() << "\n";
    ecnMarkedPackets++;
  }
  
  // Check drop threshold
  if (shouldDrop()) {
    EV << "Dropping packet " << pkt->getName() 
       << " (queue_length=" << currentQueueLength << ")\n";
    delete pkt;
    droppedPackets++;
  } else {
    enqueuePacket(pkt);
  }
  
  queueLengthVector.record(currentQueueLength);
}

bool
CongestionControl::shouldMarkECN()
{
  double load = (double)currentQueueLength / maxQueueLength;
  return load >= ecnThreshold;
}

bool
CongestionControl::shouldDrop()
{
  double load = (double)currentQueueLength / maxQueueLength;
  return load >= dropThreshold;
}

void
CongestionControl::enqueuePacket(cPacket *pkt)
{
  if (currentQueueLength >= maxQueueLength) {
    delete pkt;
    droppedPackets++;
    return;
  }
  
  currentQueueLength++;
  send(pkt, "out");
}

cPacket*
CongestionControl::dequeuePacket()
{
  if (currentQueueLength > 0) {
    currentQueueLength--;
  }
  return nullptr; // Placeholder
}

void
CongestionControl::finish()
{
  recordScalar("Total Dropped Packets", droppedPackets);
  recordScalar("Total ECN Marked Packets", ecnMarkedPackets);
  recordScalar("Final Queue Length", currentQueueLength);
  
  EV << "CongestionControl Statistics: dropped=" << droppedPackets 
     << ", ecn_marked=" << ecnMarkedPackets << "\n";
}
