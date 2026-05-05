// TrafficGenerator.h
// OMNeT++ traffic generator for HFT market data simulation.

#ifndef TRAFFIC_GENERATOR_H
#define TRAFFIC_GENERATOR_H

#include <omnetpp.h>

using namespace omnetpp;

class TrafficGenerator : public cSimpleModule
{
private:
  int numPackets;
  double interArrivalTime;
  int packetSize;
  int packetsSent;
  cMessage *sendMsg;

protected:
  virtual void initialize();
  virtual void handleMessage(cMessage *msg);
  virtual void finish();

public:
  TrafficGenerator();
  virtual ~TrafficGenerator();
};

#endif // TRAFFIC_GENERATOR_H
