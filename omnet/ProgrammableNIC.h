// ProgrammableNIC.h
// OMNeT++ module for programmable NIC with timestamp injection and packet prioritization.

#ifndef PROGRAMMABLE_NIC_H
#define PROGRAMMABLE_NIC_H

#include <omnetpp.h>

using namespace omnetpp;

class ProgrammableNIC : public cSimpleModule
{
private:
  // Parameters
  int queueSize;
  double timestampPrecisionNs;
  
  // Statistics
  cOutVector latencyVector;
  cOutVector throughputVector;
  long packetsProcessed;
  simtime_t totalLatency;
  
  // Events
  cMessage *selfMsg;

protected:
  virtual void initialize();
  virtual void handleMessage(cMessage *msg);
  virtual void finish();

  // Helper methods
  void processIncomingPacket(cPacket *pkt);
  void injectTimestamp(cPacket *pkt);
  uint64_t getNanosecondTimestamp();

public:
  ProgrammableNIC();
  virtual ~ProgrammableNIC();
};

#endif // PROGRAMMABLE_NIC_H
