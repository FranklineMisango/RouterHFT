// CongestionControl.h
// OMNeT++ module for NIC-level congestion control with ECN and queue management.

#ifndef CONGESTION_CONTROL_H
#define CONGESTION_CONTROL_H

#include <omnetpp.h>

using namespace omnetpp;

class CongestionControl : public cSimpleModule
{
private:
  // Parameters
  int maxQueueLength;
  double dropThreshold;  // Fraction of queue capacity
  double ecnThreshold;   // Fraction of queue capacity
  int currentQueueLength;
  
  // Statistics
  cOutVector queueLengthVector;
  long droppedPackets;
  long ecnMarkedPackets;

protected:
  virtual void initialize();
  virtual void handleMessage(cMessage *msg);
  virtual void finish();
  
  // Helper methods
  bool shouldDrop();
  bool shouldMarkECN();
  void enqueuePacket(cPacket *pkt);
  cPacket* dequeuePacket();

public:
  CongestionControl();
  virtual ~CongestionControl();
};

#endif // CONGESTION_CONTROL_H
