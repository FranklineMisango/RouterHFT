"""
Unit tests for the HFT Router optimization components.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.common.utils import TimestampManager, NetworkUtils, ComplianceMonitor
from src.common.compliance import ComplianceFramework, ComplianceLevel, ComplianceResult
from src.latency_mapping.ptp_timestamp import PTPClient, HighPrecisionTimer, PTPTimestamp


class TestTimestampManager:
    """Test cases for timestamp management."""
    
    def test_nanosecond_timestamp(self):
        """Test nanosecond timestamp generation."""
        ts1 = TimestampManager.get_nanosecond_timestamp()
        time.sleep(0.001)  # 1ms
        ts2 = TimestampManager.get_nanosecond_timestamp()
        
        assert ts2 > ts1
        assert (ts2 - ts1) >= 1_000_000  # At least 1ms difference
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        timestamp_ns = 1609459200_000_000_000  # 2021-01-01 00:00:00 UTC
        formatted = TimestampManager.format_timestamp(timestamp_ns)
        
        assert "2021-01-01" in formatted
        assert "00:00:00" in formatted


class TestNetworkUtils:
    """Test cases for network utilities."""
    
    def test_validate_ip_address(self):
        """Test IP address validation."""
        # Valid IPv4 addresses
        assert NetworkUtils.validate_ip_address("192.168.1.1") == True
        assert NetworkUtils.validate_ip_address("8.8.8.8") == True
        assert NetworkUtils.validate_ip_address("127.0.0.1") == True
        
        # Valid IPv6 addresses
        assert NetworkUtils.validate_ip_address("::1") == True
        assert NetworkUtils.validate_ip_address("2001:db8::1") == True
        
        # Invalid addresses
        assert NetworkUtils.validate_ip_address("300.300.300.300") == False
        assert NetworkUtils.validate_ip_address("not.an.ip") == False
        assert NetworkUtils.validate_ip_address("") == False
    
    def test_calculate_latency(self):
        """Test latency calculation."""
        start_ns = 1000_000_000
        end_ns = 1002_000_000
        
        latency_us = NetworkUtils.calculate_latency(start_ns, end_ns)
        
        assert latency_us == 2000.0  # 2ms in microseconds


class TestComplianceFramework:
    """Test cases for compliance framework."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.compliance = ComplianceFramework()
    
    def test_validate_compliant_operation(self):
        """Test validation of compliant operation."""
        operation = "research_analysis"
        params = {
            'research_only': True,
            'transparent_methodology': True
        }
        
        results = self.compliance.validate_operation(operation, params)
        
        # Should have results for all rule checks
        assert len(results) > 0
        
        # All should pass for this compliant operation
        passed_results = [r for r in results if r.passed]
        assert len(passed_results) > 0
    
    def test_validate_non_compliant_operation(self):
        """Test validation of non-compliant operation."""
        operation = "market_manipulation"
        params = {
            'research_only': False,
            'transparent_methodology': False
        }
        
        results = self.compliance.validate_operation(operation, params)
        
        # Should have violations
        violations = [r for r in results if not r.passed]
        assert len(violations) > 0
        
        # Check that violations are logged
        assert len(self.compliance.violations) > 0
    
    def test_compliance_report_generation(self):
        """Test compliance report generation."""
        # First trigger some violations
        operation = "market_manipulation"
        params = {'research_only': False}
        
        self.compliance.validate_operation(operation, params)
        
        # Generate report
        report = self.compliance.get_compliance_report()
        
        assert 'total_violations' in report
        assert 'compliance_status' in report
        assert 'detailed_violations' in report
        
        if report['total_violations'] > 0:
            assert report['compliance_status'] == 'NON_COMPLIANT'


class TestPTPTimestamp:
    """Test cases for PTP timestamp functionality."""
    
    def test_ptp_timestamp_creation(self):
        """Test PTP timestamp creation and conversion."""
        timestamp = PTPTimestamp(seconds=1609459200, nanoseconds=123456789)
        
        total_ns = timestamp.to_nanoseconds()
        expected_ns = 1609459200 * 1_000_000_000 + 123456789
        
        assert total_ns == expected_ns
    
    def test_ptp_timestamp_from_nanoseconds(self):
        """Test creating PTP timestamp from nanoseconds."""
        total_ns = 1609459200_123456789
        timestamp = PTPTimestamp.from_nanoseconds(total_ns)
        
        assert timestamp.seconds == 1609459200
        assert timestamp.nanoseconds == 123456789
    
    def test_ptp_client_initialization(self):
        """Test PTP client initialization."""
        client = PTPClient()
        
        assert client.offset_ns == 0
        assert client.is_synchronized == False
        assert client._running == False
    
    def test_high_precision_timer(self):
        """Test high precision timer functionality."""
        timer = HighPrecisionTimer()
        
        start_ts = timer.start_measurement()
        time.sleep(0.001)  # 1ms
        result = timer.end_measurement(start_ts)
        
        assert 'start_timestamp_ns' in result
        assert 'end_timestamp_ns' in result
        assert 'latency_ns' in result
        assert 'latency_us' in result
        assert 'latency_ms' in result
        
        assert result['latency_ns'] > 0
        assert result['latency_us'] > 0
        assert result['latency_ms'] > 0


class TestComplianceMonitor:
    """Test cases for compliance monitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = ComplianceMonitor()
    
    def test_cme_rule_575_check(self):
        """Test CME Rule 575 compliance check."""
        operation = "traceroute_analysis"
        params = {'target': '8.8.8.8', 'research_only': True}
        
        result = self.monitor.check_cme_rule_575(operation, params)
        
        assert isinstance(result, bool)
        # Should pass for legitimate research
        assert result == True
    
    def test_finra_rule_6140_check(self):
        """Test FINRA Rule 6140 compliance check."""
        operation = "latency_measurement"
        params = {'research_only': True}
        
        result = self.monitor.check_finra_rule_6140(operation, params)
        
        assert isinstance(result, bool)
        # Should pass for legitimate research
        assert result == True
    
    def test_sec_regulation_ats_check(self):
        """Test SEC Regulation ATS compliance check."""
        operation = "routing_analysis"
        params = {'fair_access': True}
        
        result = self.monitor.check_sec_regulation_ats(operation, params)
        
        assert isinstance(result, bool)
        # Should pass for compliant operation
        assert result == True
    
    @patch('logging.Logger.info')
    def test_operation_logging(self, mock_logger):
        """Test operation logging functionality."""
        operation = "test_operation"
        params = {'param1': 'value1'}
        
        self.monitor.log_operation(operation, params)
        
        # Verify logging was called
        mock_logger.assert_called()


class TestAsyncFunctionality:
    """Test cases for async functionality."""
    
    @pytest.mark.asyncio
    async def test_async_traceroute_simulation(self):
        """Test async traceroute simulation (mock)."""
        # This would test the actual traceroute functionality
        # For now, just test that async operations work
        
        async def mock_trace():
            await asyncio.sleep(0.01)  # Simulate network delay
            return [
                {'hop': 1, 'ip': '192.168.1.1', 'latency_ns': 1000000},
                {'hop': 2, 'ip': '8.8.8.8', 'latency_ns': 15000000}
            ]
        
        result = await mock_trace()
        
        assert len(result) == 2
        assert result[0]['hop'] == 1
        assert result[1]['hop'] == 2


# Integration tests
class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_compliance_and_timestamp_integration(self):
        """Test integration between compliance and timestamp systems."""
        compliance = ComplianceFramework()
        timestamp_mgr = TimestampManager()
        
        # Simulate a research operation with timestamp
        start_time = timestamp_mgr.get_nanosecond_timestamp()
        
        operation = "latency_research"
        params = {
            'start_timestamp': start_time,
            'research_only': True,
            'transparent_methodology': True
        }
        
        results = compliance.validate_operation(operation, params)
        
        end_time = timestamp_mgr.get_nanosecond_timestamp()
        
        # Verify integration worked
        assert len(results) > 0
        assert end_time > start_time
        
        # Should be compliant
        violations = [r for r in results if not r.passed]
        assert len(violations) == 0


# Performance tests
class TestPerformance:
    """Performance tests for critical paths."""
    
    def test_timestamp_performance(self):
        """Test timestamp generation performance."""
        iterations = 10000
        start_time = time.time()
        
        for _ in range(iterations):
            TimestampManager.get_nanosecond_timestamp()
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should be able to generate timestamps quickly
        assert elapsed < 1.0  # Less than 1 second for 10k timestamps
        
        ops_per_second = iterations / elapsed
        print(f"Timestamp generation rate: {ops_per_second:.0f} ops/sec")
    
    def test_ip_validation_performance(self):
        """Test IP validation performance."""
        test_ips = [
            "192.168.1.1", "8.8.8.8", "127.0.0.1",
            "invalid.ip", "300.300.300.300", "::1"
        ]
        
        iterations = 1000
        start_time = time.time()
        
        for _ in range(iterations):
            for ip in test_ips:
                NetworkUtils.validate_ip_address(ip)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should validate IPs quickly
        assert elapsed < 1.0  # Less than 1 second for 6k validations
        
        ops_per_second = (iterations * len(test_ips)) / elapsed
        print(f"IP validation rate: {ops_per_second:.0f} ops/sec")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
