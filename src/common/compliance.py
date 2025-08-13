"""
Compliance monitoring and validation for HFT operations.
Ensures adherence to trading regulations and ethical boundaries.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging


class ComplianceLevel(Enum):
    """Compliance check severity levels."""
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    rule: str
    level: ComplianceLevel
    message: str
    passed: bool
    details: Dict[str, Any] = None


class ComplianceFramework:
    """
    Comprehensive compliance framework for HFT router optimization.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.violations: List[ComplianceResult] = []
        
    def validate_operation(self, operation: str, params: Dict[str, Any]) -> List[ComplianceResult]:
        """
        Validate an operation against all compliance rules.
        """
        results = []
        
        # Check all regulatory frameworks
        results.extend(self._check_cme_rules(operation, params))
        results.extend(self._check_finra_rules(operation, params))
        results.extend(self._check_sec_rules(operation, params))
        results.extend(self._check_ethical_boundaries(operation, params))
        
        # Log any violations
        violations = [r for r in results if not r.passed]
        if violations:
            self.violations.extend(violations)
            for violation in violations:
                self.logger.warning(f"Compliance violation: {violation.rule} - {violation.message}")
        
        return results
    
    def _check_cme_rules(self, operation: str, params: Dict[str, Any]) -> List[ComplianceResult]:
        """Check CME Group rules compliance."""
        results = []
        
        # CME Rule 575 - Prohibited Trading Practices
        if "market_manipulation" in operation.lower():
            results.append(ComplianceResult(
                rule="CME Rule 575",
                level=ComplianceLevel.CRITICAL,
                message="Market manipulation practices are prohibited",
                passed=False
            ))
        else:
            results.append(ComplianceResult(
                rule="CME Rule 575",
                level=ComplianceLevel.INFO,
                message="No prohibited trading practices detected",
                passed=True
            ))
        
        return results
    
    def _check_finra_rules(self, operation: str, params: Dict[str, Any]) -> List[ComplianceResult]:
        """Check FINRA rules compliance."""
        results = []
        
        # FINRA Rule 6140 - Anti-Latency Arbitrage
        if params.get('latency_advantage', False) and params.get('unfair_access', False):
            results.append(ComplianceResult(
                rule="FINRA Rule 6140",
                level=ComplianceLevel.VIOLATION,
                message="Potential latency arbitrage detected",
                passed=False
            ))
        else:
            results.append(ComplianceResult(
                rule="FINRA Rule 6140",
                level=ComplianceLevel.INFO,
                message="No latency arbitrage concerns detected",
                passed=True
            ))
        
        return results
    
    def _check_sec_rules(self, operation: str, params: Dict[str, Any]) -> List[ComplianceResult]:
        """Check SEC regulations compliance."""
        results = []
        
        # SEC Regulation ATS - Fair Access
        if params.get('restricted_access', False):
            results.append(ComplianceResult(
                rule="SEC Regulation ATS",
                level=ComplianceLevel.WARNING,
                message="Ensure fair access requirements are met",
                passed=False
            ))
        else:
            results.append(ComplianceResult(
                rule="SEC Regulation ATS",
                level=ComplianceLevel.INFO,
                message="Fair access requirements satisfied",
                passed=True
            ))
        
        return results
    
    def _check_ethical_boundaries(self, operation: str, params: Dict[str, Any]) -> List[ComplianceResult]:
        """Check ethical boundaries and best practices."""
        results = []
        
        # Ensure research purposes only
        if not params.get('research_only', True):
            results.append(ComplianceResult(
                rule="Ethical Boundaries",
                level=ComplianceLevel.CRITICAL,
                message="Operations must be for research purposes only",
                passed=False
            ))
        
        # Check for transparency
        if not params.get('transparent_methodology', True):
            results.append(ComplianceResult(
                rule="Ethical Boundaries",
                level=ComplianceLevel.WARNING,
                message="Methodology should be transparent and documented",
                passed=False
            ))
        
        return results
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive compliance report."""
        total_checks = len(self.violations) if self.violations else 0
        violations_by_level = {}
        
        for violation in self.violations:
            level = violation.level.value
            violations_by_level[level] = violations_by_level.get(level, 0) + 1
        
        return {
            'total_violations': len(self.violations),
            'violations_by_level': violations_by_level,
            'compliance_status': 'COMPLIANT' if not self.violations else 'NON_COMPLIANT',
            'detailed_violations': [
                {
                    'rule': v.rule,
                    'level': v.level.value,
                    'message': v.message,
                    'details': v.details
                } for v in self.violations
            ]
        }
