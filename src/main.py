"""
Main entry point for the HFT Router Optimization system.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
import yaml

# Add src to path
sys.path.append(str(Path(__file__).parent))

from common.utils import setup_logging, ComplianceMonitor, TimestampManager
from common.compliance import ComplianceFramework
from latency_mapping.traceroute_analyzer import PTPTimestampTracer, LatencyAnalyzer
from latency_mapping.ptp_timestamp import TimeSyncManager
from latency_mapping.geo_visualizer import NetworkPathVisualizer
from bgp_simulation.routing_sim import BGPSimulator, RouteOptimizer


class HFTRouterSystem:
    """
    Main system orchestrator for HFT Router optimization.
    """
    
    def __init__(self, config_path: str = "configs/hft_config.yaml"):
        self.config_path = config_path
        self.config = None
        self.logger = None
        self.running = False
        
        # Core components
        self.compliance_framework = None
        self.compliance_monitor = None
        self.time_sync_manager = None
        self.tracer = None
        self.visualizer = None
        self.bgp_simulator = None
        
    async def initialize(self) -> bool:
        """
        Initialize the HFT Router system.
        """
        try:
            # Load configuration
            await self._load_configuration()
            
            # Setup logging
            setup_logging(self.config.get('logging', {}).get('level', 'INFO'))
            self.logger = logging.getLogger(__name__)
            self.logger.info("Initializing HFT Router Optimization System")
            
            # Initialize compliance framework
            self.compliance_framework = ComplianceFramework()
            self.compliance_monitor = ComplianceMonitor()
            
            # Initialize time synchronization
            self.time_sync_manager = TimeSyncManager()
            ptp_master = self.config.get('network', {}).get('ptp', {}).get('master_ip')
            time_sync_success = self.time_sync_manager.initialize_time_sync(ptp_master)
            
            if time_sync_success:
                self.logger.info("Time synchronization established")
            else:
                self.logger.warning("Time synchronization failed, using system time")
            
            # Initialize network components
            self.tracer = PTPTimestampTracer(self.compliance_monitor)
            self.visualizer = NetworkPathVisualizer()
            self.bgp_simulator = BGPSimulator(self.compliance_framework)
            
            self.logger.info("HFT Router system initialized successfully")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize system: {e}")
            else:
                print(f"Failed to initialize system: {e}")
            return False
    
    async def _load_configuration(self) -> None:
        """
        Load system configuration from YAML file.
        """
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Use default configuration
                self.config = self._get_default_config()
                
        except Exception as e:
            self.config = self._get_default_config()
            if hasattr(self, 'logger') and self.logger:
                self.logger.warning(f"Failed to load config, using defaults: {e}")
    
    def _get_default_config(self) -> dict:
        """
        Get default configuration.
        """
        return {
            'logging': {'level': 'INFO'},
            'network': {
                'ptp': {'master_ip': None},
                'interfaces': {'primary': 'eth0'}
            },
            'latency_mapping': {
                'max_hops': 30,
                'timeout_seconds': 5,
                'target_exchanges': []
            },
            'compliance': {
                'mode': 'strict',
                'log_all_operations': True
            }
        }
    
    async def run_latency_analysis(self, targets: list = None) -> dict:
        """
        Run comprehensive latency analysis.
        """
        if not targets:
            targets = self._get_target_exchanges()
        
        results = {}
        analyzer = LatencyAnalyzer()
        
        self.logger.info(f"Starting latency analysis for {len(targets)} targets")
        
        for target in targets:
            try:
                self.logger.info(f"Analyzing route to {target}")
                
                # Perform traceroute analysis
                hops = await self.tracer.trace_route_async(target)
                
                # Analyze results
                analysis = analyzer.analyze_hop_latencies(hops)
                
                # Create visualizations
                interactive_map = self.visualizer.create_interactive_map(hops, f"Route to {target}")
                dashboard = self.visualizer.create_latency_dashboard(hops)
                
                results[target] = {
                    'hops': hops,
                    'analysis': analysis,
                    'visualizations': {
                        'map': interactive_map,
                        'dashboard': dashboard
                    }
                }
                
                self.logger.info(f"Completed analysis for {target}: {len(hops)} hops, "
                                f"{analysis.get('total_latency_us', 0):.2f}μs total latency")
                
            except Exception as e:
                self.logger.error(f"Failed to analyze route to {target}: {e}")
                results[target] = {'error': str(e)}
        
        return results
    
    async def run_bgp_simulation(self, scenarios: list = None) -> dict:
        """
        Run BGP routing simulations.
        """
        if not scenarios:
            scenarios = ['financial_exchange', 'microwave_backup']
        
        results = {}
        optimizer = RouteOptimizer()
        
        self.logger.info(f"Starting BGP simulation for {len(scenarios)} scenarios")
        
        for scenario_name in scenarios:
            try:
                # Create simulation scenario
                topology = self._get_simulation_topology(scenario_name)
                simulation_id = self.bgp_simulator.create_simulation_scenario(
                    scenario_name, topology
                )
                
                # Run simulation
                sim_result = self.bgp_simulator.run_simulation(simulation_id)
                
                results[scenario_name] = {
                    'simulation_id': simulation_id,
                    'result': sim_result,
                    'topology': topology
                }
                
                self.logger.info(f"Completed BGP simulation {scenario_name}: "
                                f"{sim_result.convergence_time_ms:.1f}ms convergence")
                
            except Exception as e:
                self.logger.error(f"Failed to run BGP simulation {scenario_name}: {e}")
                results[scenario_name] = {'error': str(e)}
        
        # Analyze all results
        if results:
            sim_results = [r['result'] for r in results.values() if 'result' in r]
            if sim_results:
                optimization_analysis = optimizer.analyze_simulation_results(sim_results)
                results['optimization_analysis'] = optimization_analysis
        
        return results
    
    def _get_target_exchanges(self) -> list:
        """
        Get target exchanges from configuration.
        """
        exchanges = self.config.get('latency_mapping', {}).get('target_exchanges', [])
        return [exchange.get('ip', '8.8.8.8') for exchange in exchanges]
    
    def _get_simulation_topology(self, scenario_name: str) -> dict:
        """
        Get simulation topology for a scenario.
        """
        topologies = {
            'financial_exchange': {
                'router_id': '10.1.1.1',
                'as_number': 65001,
                'networks': ['10.1.0.0/16'],
                'neighbors': [
                    {'ip': '10.1.1.2', 'as_number': 65002, 'name': 'exchange_1'},
                    {'ip': '10.1.1.3', 'as_number': 65003, 'name': 'exchange_2'}
                ]
            },
            'microwave_backup': {
                'router_id': '10.2.1.1',
                'as_number': 65010,
                'networks': ['10.2.0.0/16'],
                'neighbors': [
                    {'ip': '10.2.1.2', 'as_number': 65020, 'name': 'fiber_primary'},
                    {'ip': '10.2.1.3', 'as_number': 65021, 'name': 'microwave_backup'}
                ]
            }
        }
        
        return topologies.get(scenario_name, topologies['financial_exchange'])
    
    async def generate_compliance_report(self) -> dict:
        """
        Generate comprehensive compliance report.
        """
        self.logger.info("Generating compliance report")
        
        report = self.compliance_framework.get_compliance_report()
        
        # Add system status
        report['system_status'] = {
            'time_synchronized': self.time_sync_manager.ptp_client.is_synchronized,
            'components_operational': {
                'tracer': self.tracer is not None,
                'visualizer': self.visualizer is not None,
                'bgp_simulator': self.bgp_simulator is not None
            }
        }
        
        return report
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the system.
        """
        self.logger.info("Shutting down HFT Router system")
        self.running = False
        
        # Shutdown time synchronization
        if self.time_sync_manager:
            self.time_sync_manager.shutdown()
        
        self.logger.info("System shutdown complete")
    
    async def run(self) -> None:
        """
        Main system run loop.
        """
        self.running = True
        self.logger.info("HFT Router system starting main loop")
        
        try:
            # Run initial analysis
            latency_results = await self.run_latency_analysis()
            bgp_results = await self.run_bgp_simulation()
            
            # Generate reports
            compliance_report = await self.generate_compliance_report()
            
            # Log summary
            self.logger.info("Initial analysis complete:")
            self.logger.info(f"- Latency analysis: {len(latency_results)} targets")
            self.logger.info(f"- BGP simulations: {len(bgp_results)} scenarios")
            self.logger.info(f"- Compliance status: {compliance_report.get('compliance_status', 'UNKNOWN')}")
            
            # Keep running for monitoring (simplified)
            while self.running:
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()


async def main():
    """
    Main entry point.
    """
    system = HFTRouterSystem()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down...")
        system.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize and run system
    if await system.initialize():
        await system.run()
    else:
        print("Failed to initialize system")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
