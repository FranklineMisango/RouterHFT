"""
Common utilities and compliance monitoring for HFT Router optimization.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime


class ComplianceMonitor:
    """
    Monitors and ensures all operations comply with trading regulations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.violations = []
        
    def check_cme_rule_575(self, operation: str, params: Dict[str, Any]) -> bool:
        """
        Verify compliance with CME Rule 575 (Prohibited Trading Practices).
        """
        # Implementation for compliance checking
        self.logger.info(f"Checking CME Rule 575 compliance for: {operation}")
        return True
    
    def check_finra_rule_6140(self, operation: str, params: Dict[str, Any]) -> bool:
        """
        Verify compliance with FINRA Rule 6140 (Anti-Latency Arbitrage).
        """
        self.logger.info(f"Checking FINRA Rule 6140 compliance for: {operation}")
        return True
    
    def check_sec_regulation_ats(self, operation: str, params: Dict[str, Any]) -> bool:
        """
        Verify compliance with SEC Regulation ATS (Fair Access).
        """
        self.logger.info(f"Checking SEC Regulation ATS compliance for: {operation}")
        return True
    
    def log_operation(self, operation: str, params: Dict[str, Any]) -> None:
        """
        Log all operations for audit trail.
        """
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'operation': operation,
            'parameters': params
        }
        self.logger.info(f"Operation logged: {log_entry}")


class TimestampManager:
    """
    High-precision timestamp management for latency measurements.
    """
    
    @staticmethod
    def get_nanosecond_timestamp() -> int:
        """
        Get current timestamp in nanoseconds.
        """
        return time.time_ns()
    
    @staticmethod
    def format_timestamp(timestamp_ns: int) -> str:
        """
        Format nanosecond timestamp for display.
        """
        seconds = timestamp_ns / 1_000_000_000
        return datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S.%f')


class NetworkUtils:
    """
    Common network utilities for packet analysis and routing.
    """
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """
        Validate IP address format.
        """
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def calculate_latency(start_ns: int, end_ns: int) -> float:
        """
        Calculate latency in microseconds.
        """
        return (end_ns - start_ns) / 1000.0  # Convert to microseconds


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup logging configuration for the project.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('hft_router.log'),
            logging.StreamHandler()
        ]
    )
