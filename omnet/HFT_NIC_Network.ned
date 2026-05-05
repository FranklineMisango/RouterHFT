// HFT_NIC_Network.ned
// OMNeT++ network definition for HFT NIC simulation with congestion control.

package routerhft.nic;

simple TrafficGenerator
{
    parameters:
        int numPackets = default(1000);
        double interArrivalTime @unit(s) = default(1ms);
        int packetSize @unit(B) = default(256);
    gates:
        output out;
}

simple ProgrammableNIC
{
    parameters:
        int queueSize = default(1024);
        double timestampPrecisionNs @unit(ns) = default(1);
        @display("i=device/nic");
    gates:
        input in;
        output out;
}

simple CongestionControl
{
    parameters:
        int maxQueueLength = default(512);
        double dropThreshold = default(0.9);  // drop if queue > 90%
        double ecnThreshold = default(0.5);   // ECN mark if queue > 50%
        @display("i=block/queue");
    gates:
        input in;
        output out;
}

simple PacketSink
{
    parameters:
        @display("i=sink");
    gates:
        input in;
}

network HFT_NIC_Network
{
    submodules:
        gen: TrafficGenerator {
            @display("p=50,100");
        }
        nic: ProgrammableNIC {
            @display("p=150,100");
        }
        cc: CongestionControl {
            @display("p=250,100");
        }
        sink: PacketSink {
            @display("p=350,100");
        }
    
    connections:
        gen.out --> nic.in;
        nic.out --> cc.in;
        cc.out --> sink.in;
}
