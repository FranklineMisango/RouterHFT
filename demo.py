#!/usr/bin/env python3
"""
Optional legacy helper for HFT Router Optimization charts/visualization.

Primary testing for this repo is C++-first; use tests/cpp/hft_smoke_test.cpp
for the main verification path.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.common.utils import TimestampManager, ComplianceMonitor, setup_logging
from src.common.compliance import ComplianceFramework
from src.latency_mapping.ptp_timestamp import TimeSyncManager, HighPrecisionTimer


async def demo_timestamp_precision():
    """Demo high-precision timestamp functionality."""
    print("Testing High-Precision Timestamps")
    print("=" * 50)
    
    # Basic timestamp
    ts1 = TimestampManager.get_nanosecond_timestamp()
    await asyncio.sleep(0.001)  # 1ms delay
    ts2 = TimestampManager.get_nanosecond_timestamp()
    
    latency_ns = ts2 - ts1
    latency_us = latency_ns / 1000.0
    
    print(f"Start timestamp: {ts1:,} ns")
    print(f"End timestamp:   {ts2:,} ns")
    print(f"Measured latency: {latency_ns:,} ns ({latency_us:.2f} μs)")
    print()


def demo_compliance_framework():
    """Demo compliance framework functionality."""
    print("Testing Compliance Framework")
    print("=" * 50)
    
    compliance = ComplianceFramework()
    
    # Test compliant operation
    print("Testing compliant research operation...")
    operation = "latency_research"
    params = {
        'research_only': True,
        'transparent_methodology': True,
        'target': '8.8.8.8'
    }
    
    results = compliance.validate_operation(operation, params)
    passed_checks = sum(1 for r in results if r.passed)
    total_checks = len(results)
    
    print(f"Compliance checks: {passed_checks}/{total_checks} passed")
    
    # Test non-compliant operation
    print("\nTesting non-compliant operation...")
    bad_operation = "market_manipulation"
    bad_params = {
        'research_only': False,
        'unfair_access': True
    }
    
    bad_results = compliance.validate_operation(bad_operation, bad_params)
    violations = [r for r in bad_results if not r.passed]
    
    print(f"Violations detected: {len(violations)}")
    for violation in violations:
        print(f"  - {violation.rule}: {violation.message}")
    
    # Generate compliance report
    report = compliance.get_compliance_report()
    print(f"\nCompliance Status: {report['compliance_status']}")
    print()


async def demo_time_synchronization():
    """Demo time synchronization functionality."""
    print("Testing Time Synchronization")
    print("=" * 50)
    
    time_mgr = TimeSyncManager()
    
    # Initialize without PTP master (uses system time)
    success = time_mgr.initialize_time_sync()
    print(f"Time sync initialized: {success}")
    
    # Create high-precision timer
    timer = time_mgr.create_timer()
    
    # Measure a small operation
    start_ts = timer.start_measurement()
    
    # Simulate some work
    test_data = [i**2 for i in range(1000)]
    sum_result = sum(test_data)
    
    measurement = timer.end_measurement(start_ts)
    
    print(f"Operation completed:")
    print(f"  Duration: {measurement['latency_ns']:,} ns")
    print(f"  Duration: {measurement['latency_us']:.2f} μs")
    print(f"  Duration: {measurement['latency_ms']:.4f} ms")
    print(f"  Synchronized: {measurement['synchronized']}")
    print(f"  Result: {sum_result:,}")
    
    time_mgr.shutdown()
    print()


async def demo_network_validation():
    """Demo network utilities."""
    print("Testing Network Utilities")
    print("=" * 50)
    
    from src.common.utils import NetworkUtils
    
    test_ips = [
        "8.8.8.8",           # Valid
        "192.168.1.1",       # Valid
        "::1",               # Valid IPv6
        "300.300.300.300",   # Invalid
        "not.an.ip",         # Invalid
    ]
    
    print("IP Address Validation:")
    for ip in test_ips:
        valid = NetworkUtils.validate_ip_address(ip)
        status = "✅ Valid" if valid else "❌ Invalid"
        print(f"  {ip:<20} {status}")
    
    print("\nLatency Calculation Test:")
    start_ns = 1000_000_000
    end_ns = 1015_000_000
    latency = NetworkUtils.calculate_latency(start_ns, end_ns)
    print(f"  Start: {start_ns:,} ns")
    print(f"  End:   {end_ns:,} ns")
    print(f"  Latency: {latency:.1f} μs")
    print()


async def main():
    """Main demo function."""
    print("HFT Router Optimization System Demo")
    print("=" * 60)
    print()
    
    # Setup logging
    setup_logging()
    
    try:
        # Run demos
        await demo_timestamp_precision()
        demo_compliance_framework()
        await demo_time_synchronization()
        await demo_network_validation()
        
        print("All demos completed successfully!")
        print()
        print("Next steps:")
        print("1. Configure target exchanges in configs/hft_config.yaml")
        print("2. Run: python -m src.main")
        print("3. Check the generated visualizations")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
