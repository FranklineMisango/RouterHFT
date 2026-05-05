// PacketSink.h
// OMNeT++ packet sink for collecting and analyzing received packets.

#ifndef PACKET_SINK_H
#define PACKET_SINK_H

#include <omnetpp.h>

using namespace omnetpp;

class PacketSink : public cSimpleModule
{
private:
  long packetsReceived;
  long totalBytesReceived;

protected:
  virtual void initialize();
  virtual void handleMessage(cMessage *msg);
  virtual void finish();

public:
  PacketSink();
  virtual ~PacketSink();
};

#endif // PACKET_SINK_H
