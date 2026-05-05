// ProgrammableNIC.cc
// OMNeT++ implementation of a programmable NIC with nanosecond timestamp injection.

#include "ProgrammableNIC.h"
#include <ctime>

Define_Module(ProgrammableNIC);

ProgrammableNIC::ProgrammableNIC()
{
  selfMsg = nullptr;
  packetsProcessed = 0;
  totalLatency = 0;
}

ProgrammableNIC::~ProgrammableNIC()
{
  cancelAndDelete(selfMsg);
}

void
ProgrammableNIC::initialize()
{
  queueSize = par("queueSize").intValue();
  timestampPrecisionNs = par("timestampPrecisionNs").doubleValue();
  
  latencyVector.setName("NIC_Latency");
  throughputVector.setName("NIC_Throughput");
  
  selfMsg = new cMessage("NIC_SelfMsg");
  
  EV << "ProgrammableNIC initialized: queue=" << queueSize 
     << ", precision=" << timestampPrecisionNs << "ns\n";
}

void
ProgrammableNIC::handleMessage(cMessage *msg)
{
  if (msg == selfMsg) {
    EV << "NIC self-message triggered\n";
    // Placeholder for internal NIC events (e.g., queue management)
  } else if (msg->isSelfMessage()) {
    delete msg;
  } else {
    // Incoming packet from network
    cPacket *pkt = check_and_cast<cPacket*>(msg);
    processIncomingPacket(pkt);
  }
}

void
ProgrammableNIC::processIncomingPacket(cPacket *pkt)
{
  // Inject nanosecond timestamp
  injectTimestamp(pkt);
  
  // Record statistics
  simtime_t latency = simTime() - pkt->getCreationTime();
  latencyVector.record(latency.dbl());
  totalLatency += latency;
  packetsProcessed++;
  
  EV << "NIC processed packet: " << pkt->getName() 
     << " (latency=" << latency.str() << ")\n";
  
  // Forward to output gate (placeholder: send to routing layer)
  send(pkt, "out");
}

void
ProgrammableNIC::injectTimestamp(cPacket *pkt)
{
  uint64_t ts_ns = getNanosecondTimestamp();
  // TODO: attach as custom packet field or header
  EV << "Injected timestamp: " << ts_ns << " ns\n";
}

uint64_t
ProgrammableNIC::getNanosecondTimestamp()
{
  // Return current simulation time in nanoseconds
  return (uint64_t)(simTime().dbl() * 1e9);
}

void
ProgrammableNIC::finish()
{
  recordScalar("Total Packets Processed", packetsProcessed);
  if (packetsProcessed > 0) {
    recordScalar("Average Latency (ns)", (totalLatency.dbl() / packetsProcessed) * 1e9);
  }
  
  EV << "NIC Statistics: processed=" << packetsProcessed 
     << ", avg_latency=" << (totalLatency.dbl() / (packetsProcessed ?: 1)) * 1e9 << "ns\n";
}
