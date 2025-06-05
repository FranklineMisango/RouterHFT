# HFT Router Latency Optimization Research

A collection of tools and research materials for analyzing and optimizing network latency in high-frequency trading environments, with strict adherence to legal and ethical boundaries.

## Projects

### 1. Latency Mapping Tool
Visualizes router hop latency between major financial exchanges using traceroute with PTP-synchronized timestamps.

**Features**:
- Nanosecond-precision latency measurement
- Geographic visualization of network paths
- Microwave tower location overlay (FCC data)

### 2. FPGA Packet Prioritization
Hardware-accelerated market data packet processing using Verilog/VHDL.

**Components**:
- NetFPGA/Xilinx Alveo implementation
- PCIe DMA bypass for low-latency
- Exchange-specific packet tagging

### 3. BGP Route Simulation
Linux-based BGP routing simulation for hypothetical latency analysis.

**Methodology**:
- Bird/Quagga routing daemons
- Real-world latency benchmarking
- Alternative route comparison

## Legal Compliance
All projects strictly follow:
- CME Rule 575 (Prohibited Trading Practices)
- FINRA Rule 6140 (Anti-Latency Arbitrage)
- SEC Regulation ATS (Fair Access)


## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/HFT-Router-Optimization/main.git
```

2. Basic packet capture example:
```
from scapy.all import sniff  
import time  

def packet_callback(pkt):  
    print(f"[{time.time_ns()}] Packet to {pkt[IP].dst}")  

sniff(filter="ip dst 192.168.1.100", prn=packet_callback)
```
