"""
High-precision traceroute analyzer with PTP-synchronized timestamps.
Measures nanosecond-level latency between network hops.
"""

import subprocess
import time
import socket
import struct
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from scapy.all import *
import asyncio
import logging

from ..common.utils import TimestampManager, ComplianceMonitor, NetworkUtils


@dataclass
class HopData:
    """Data structure for a single network hop."""
    hop_number: int
    ip_address: str
    hostname: Optional[str]
    rtt_ns: int
    timestamp_ns: int
    geographic_location: Optional[Tuple[float, float]] = None


class PTPTimestampTracer:
    """
    Advanced traceroute implementation with PTP-synchronized timestamps.
    """
    
    def __init__(self, compliance_monitor: ComplianceMonitor):
        self.compliance_monitor = compliance_monitor
        self.logger = logging.getLogger(__name__)
        self.timestamp_manager = TimestampManager()
        
    async def trace_route_async(self, target: str, max_hops: int = 30) -> List[HopData]:
        """
        Perform asynchronous traceroute with nanosecond precision.
        """
        # Compliance check
        operation_params = {
            'target': target,
            'max_hops': max_hops,
            'research_only': True,
            'transparent_methodology': True
        }
        
        if not self._validate_compliance("traceroute_analysis", operation_params):
            raise ValueError("Operation failed compliance check")
        
        hops = []
        
        for ttl in range(1, max_hops + 1):
            hop_data = await self._trace_single_hop(target, ttl)
            if hop_data:
                hops.append(hop_data)
                
                # Check if we've reached the target
                if hop_data.ip_address == target:
                    break
                    
        return hops
    
    async def _trace_single_hop(self, target: str, ttl: int) -> Optional[HopData]:
        """
        Trace a single hop with precise timing.
        """
        try:
            # Create ICMP packet with specific TTL
            packet = IP(dst=target, ttl=ttl) / ICMP()
            
            # Record precise send timestamp
            send_timestamp = self.timestamp_manager.get_nanosecond_timestamp()
            
            # Send packet and wait for response
            response = sr1(packet, timeout=3, verbose=0)
            
            # Record precise receive timestamp
            recv_timestamp = self.timestamp_manager.get_nanosecond_timestamp()
            
            if response:
                rtt_ns = recv_timestamp - send_timestamp
                ip_addr = response.src
                hostname = self._resolve_hostname(ip_addr)
                
                return HopData(
                    hop_number=ttl,
                    ip_address=ip_addr,
                    hostname=hostname,
                    rtt_ns=rtt_ns,
                    timestamp_ns=send_timestamp
                )
                
        except Exception as e:
            self.logger.error(f"Error tracing hop {ttl}: {e}")
            
        return None
    
    def _resolve_hostname(self, ip_address: str) -> Optional[str]:
        """
        Resolve IP address to hostname with timeout.
        """
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            return hostname
        except (socket.herror, socket.gaierror):
            return None
    
    def _validate_compliance(self, operation: str, params: Dict) -> bool:
        """
        Validate operation against compliance rules.
        """
        try:
            # Check all compliance rules
            cme_check = self.compliance_monitor.check_cme_rule_575(operation, params)
            finra_check = self.compliance_monitor.check_finra_rule_6140(operation, params)
            sec_check = self.compliance_monitor.check_sec_regulation_ats(operation, params)
            
            # Log the operation
            self.compliance_monitor.log_operation(operation, params)
            
            return cme_check and finra_check and sec_check
            
        except Exception as e:
            self.logger.error(f"Compliance validation failed: {e}")
            return False


class LatencyAnalyzer:
    """
    Analyzes latency patterns and identifies optimization opportunities.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_hop_latencies(self, hops: List[HopData]) -> Dict[str, any]:
        """
        Analyze latency patterns across network hops.
        """
        if not hops:
            return {}
        
        latencies_us = [hop.rtt_ns / 1000.0 for hop in hops]  # Convert to microseconds
        
        analysis = {
            'total_hops': len(hops),
            'total_latency_us': sum(latencies_us),
            'average_hop_latency_us': sum(latencies_us) / len(latencies_us),
            'max_latency_hop': max(hops, key=lambda h: h.rtt_ns),
            'min_latency_hop': min(hops, key=lambda h: h.rtt_ns),
            'latency_variance': self._calculate_variance(latencies_us),
            'optimization_opportunities': self._identify_optimization_opportunities(hops)
        }
        
        return analysis
    
    def _calculate_variance(self, latencies: List[float]) -> float:
        """
        Calculate variance in latency measurements.
        """
        if len(latencies) < 2:
            return 0.0
        
        mean = sum(latencies) / len(latencies)
        variance = sum((x - mean) ** 2 for x in latencies) / len(latencies)
        return variance
    
    def _identify_optimization_opportunities(self, hops: List[HopData]) -> List[Dict[str, any]]:
        """
        Identify potential optimization opportunities in the route.
        """
        opportunities = []
        
        for i, hop in enumerate(hops):
            # Identify high-latency hops
            if hop.rtt_ns > 10_000_000:  # > 10ms
                opportunities.append({
                    'type': 'high_latency_hop',
                    'hop_number': hop.hop_number,
                    'ip_address': hop.ip_address,
                    'latency_us': hop.rtt_ns / 1000.0,
                    'recommendation': 'Consider alternative routing'
                })
            
            # Identify geographic inefficiencies
            if hop.geographic_location and i > 0:
                # Add geographic analysis logic here
                pass
        
        return opportunities


# Usage example and testing functions
async def main():
    """
    Example usage of the traceroute analyzer.
    """
    from ..common.utils import setup_logging
    
    setup_logging()
    compliance_monitor = ComplianceMonitor()
    tracer = PTPTimestampTracer(compliance_monitor)
    analyzer = LatencyAnalyzer()
    
    # Example: Trace route to a financial exchange (simulated)
    target = "8.8.8.8"  # Using Google DNS as example
    
    print(f"Tracing route to {target}...")
    hops = await tracer.trace_route_async(target)
    
    print(f"Completed trace with {len(hops)} hops")
    
    # Analyze the results
    analysis = analyzer.analyze_hop_latencies(hops)
    print(f"Analysis: {analysis}")


if __name__ == "__main__":
    asyncio.run(main())
