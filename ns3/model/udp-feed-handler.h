// udp-feed-handler.h
// NS-3 application for high-frequency trading UDP feed handler with nanosecond timestamps.

#ifndef UDP_FEED_HANDLER_H
#define UDP_FEED_HANDLER_H

#include "ns3/application.h"
#include "ns3/event-id.h"
#include "ns3/ptr.h"
#include "ns3/socket.h"
#include "ns3/address.h"
#include "ns3/traced-callback.h"
#include "ns3/core-module.h"

namespace ns3 {

class Socket;

class UDPFeedHandler : public Application
{
public:
  static TypeId GetTypeId(void);
  UDPFeedHandler();
  virtual ~UDPFeedHandler();

  void Setup(Ptr<Socket> socket, Address address, uint32_t packetSize, DataRate dataRate);
  void Setup(Address address, uint16_t port, uint32_t packetSize, Time interPacketGap);

protected:
  virtual void StartApplication(void);
  virtual void StopApplication(void);

private:
  void ScheduleTransmit(Time dt);
  void SendPacket(void);
  uint64_t GetNanosecondTimestamp(void);

  Ptr<Socket> m_socket;
  Address m_peer;
  uint32_t m_packetSize;
  uint32_t m_dataRate;
  Time m_interPacketGap;
  EventId m_sendEvent;
  bool m_running;
  uint32_t m_packetCount;

  TracedCallback<Ptr<const Packet> > m_txTrace;
};

} // namespace ns3

#endif // UDP_FEED_HANDLER_H
