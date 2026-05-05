#!/usr/bin/env python3
"""
RouterHFT Simulation Runner & Parameter Tuner

Interactive script to run NS-3 simulations with custom parameters,
collect results, and visualize them.

Usage:
  python3 run_simulation.py                          # Interactive mode
  python3 run_simulation.py --preset benchmark       # Use a preset
  python3 run_simulation.py --list-presets           # List available presets
"""

import argparse
import csv
import os
import shutil
import stat
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
SIM_SOURCE = ROOT / "simulations" / "nic_router_pipeline.cc"
RESULTS_DIR = ROOT / "results"
SCRIPTS_DIR = ROOT / "scripts"

# ---------------------------------------------------------------------------
# Parameter definitions
# ---------------------------------------------------------------------------
@dataclass
class SimParams:
    """All tunable simulation parameters with their defaults and descriptions."""

    # --- Network ---
    link_rate: str = "10Gbps"
    """Data rate on both P2P links. Options: 1Gbps, 10Gbps, 40Gbps, 100Gbps"""

    link_delay: str = "10us"
    """Propagation delay per link. Options: 1us, 5us, 10us, 50us, 100us, 1ms"""

    # --- Traffic ---
    packet_count: int = 30000
    """Total number of UDP packets to send from generator to sink"""

    packet_size: int = 256
    """UDP payload size in bytes. Typical: 64-1500"""

    inter_packet_gap_us: int = 50
    """Gap between packets in microseconds. Lower = higher data rate."""

    # --- Simulation ---
    sim_stop_seconds: float = 5.0
    """How long the simulator runs (wall-clock simulated time)."""

    # --- OMNeT++ congestion ---
    ecn_threshold: float = 0.70
    """Queue occupancy fraction at which ECN marking begins (OMNeT CC)"""

    drop_threshold: float = 0.95
    """Queue occupancy fraction at which packets are dropped (OMNeT CC)"""

    queue_size: int = 2048
    """NIC queue size in packets (OMNeT ProgrammableNIC)"""

    def pps(self) -> float:
        """Theoretical packets-per-second from the inter-packet gap."""
        return 1_000_000 / self.inter_packet_gap_us

    def data_rate_mbps(self) -> float:
        """Theoretical data rate in Mbps."""
        return self.pps() * self.packet_size * 8 / 1_000_000

    def cmdline_args(self) -> List[str]:
        return [
            f"--linkRate={self.link_rate}",
            f"--linkDelay={self.link_delay}",
            f"--packetCount={self.packet_count}",
            f"--packetSize={self.packet_size}",
            f"--intervalUs={self.inter_packet_gap_us}",
            f"--simulationStopSeconds={self.sim_stop_seconds}",
        ]

    def summary_line(self) -> str:
        return (
            f"rate={self.link_rate}  delay={self.link_delay}  "
            f"pkts={self.packet_count}  size={self.packet_size}B  "
            f"gap={self.inter_packet_gap_us}us  "
            f"stop={self.sim_stop_seconds}s  "
            f"[~{self.pps():.0f} pps, ~{self.data_rate_mbps():.1f} Mbps]"
        )


# ---------------------------------------------------------------------------
# Preset configurations
# ---------------------------------------------------------------------------
PRESETS: Dict[str, SimParams] = {
    "baseline": SimParams(
        link_rate="10Gbps",
        link_delay="10us",
        packet_count=30000,
        packet_size=256,
        inter_packet_gap_us=50,
        sim_stop_seconds=5.0,
    ),
    "high-throughput": SimParams(
        link_rate="40Gbps",
        link_delay="5us",
        packet_count=100000,
        packet_size=64,  # small packets, high message rate
        inter_packet_gap_us=10,  # ~100K pps
        sim_stop_seconds=8.0,
    ),
    "long-haul": SimParams(
        link_rate="10Gbps",
        link_delay="100us",  # simulate geographic distance
        packet_count=20000,
        packet_size=512,
        inter_packet_gap_us=100,
        sim_stop_seconds=8.0,
    ),
    "congestion-stress": SimParams(
        link_rate="1Gbps",  # bottleneck
        link_delay="10us",
        packet_count=50000,
        packet_size=1024,  # large packets
        inter_packet_gap_us=5,  # very fast = backpressure
        sim_stop_seconds=10.0,
    ),
    "burst": SimParams(
        link_rate="10Gbps",
        link_delay="10us",
        packet_count=5000,
        packet_size=1500,  # MTU-sized
        inter_packet_gap_us=1,  # 1M pps microburst
        sim_stop_seconds=3.0,
    ),
    "hft-co-lo": SimParams(
        link_rate="100Gbps",
        link_delay="1us",  # co-location latency
        packet_count=1000000,
        packet_size=128,
        inter_packet_gap_us=1,  # 1M pps
        sim_stop_seconds=12.0,
    ),
}


# ---------------------------------------------------------------------------
# Analysis helper files
# ---------------------------------------------------------------------------
@dataclass
class Analysis:
    name: str
    params: SimParams
    latency_stats: dict = field(default_factory=dict)
    throughput_stats: dict = field(default_factory=dict)
    run_dir: Path = Path()

    def summary(self) -> str:
        lines = [
            f"--- {self.name} ---",
            f"  Config: {self.params.summary_line()}",
            "",
            "  Latency (ns):",
        ]
        if self.latency_stats:
            ls = self.latency_stats
            lines.append(f"    Count:  {ls['count']}")
            lines.append(f"    Min:    {ls['min']:>10.0f}")
            lines.append(f"    Mean:   {ls['mean']:>10.0f}")
            lines.append(f"    Median: {ls['p50']:>10.0f}")
            lines.append(f"    P99:    {ls['p99']:>10.0f}")
            lines.append(f"    P99.9:  {ls['p999']:>10.0f}")
            lines.append(f"    Max:    {ls['max']:>10.0f}")
            lines.append(f"    Std:    {ls['std']:>10.0f}")
            lines.append(f"    Jitter: {ls['jitter_ns']:>10.0f}")
        else:
            lines.append("    (no data)")

        lines.append("")
        lines.append("  Throughput:")
        if self.throughput_stats and self.throughput_stats.get("entries"):
            ts = self.throughput_stats
            lines.append(f"    Seconds with data: {ts['entries']}")
            lines.append(f"    Peak pps:          {ts['peak_pps']:>10.0f}")
            lines.append(f"    Avg pps:           {ts['avg_pps']:>10.0f}")
            lines.append(f"    Total packets rx:  {ts['total_packets']:>10.0f}")
        else:
            lines.append("    (no data)")

        lines.append("")
        return "\n".join(lines)


def analyze_latency(csv_path: Path) -> Optional[dict]:
    if not csv_path.exists():
        return None
    latencies = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            latencies.append(int(row["latency_ns"]))
    if not latencies:
        return None
    n = len(latencies)
    s = sorted(latencies)
    mean = sum(s) / n
    variance = sum((x - mean) ** 2 for x in s) / n
    return {
        "count": n,
        "min": s[0],
        "max": s[-1],
        "mean": mean,
        "p50": s[int(n * 0.50)],
        "p90": s[int(n * 0.90)],
        "p95": s[int(n * 0.95)],
        "p99": s[int(n * 0.99)],
        "p999": s[int(n * 0.999)],
        "std": variance ** 0.5,
        "jitter_ns": s[-1] - s[0],
    }


def analyze_throughput(csv_path: Path) -> Optional[dict]:
    if not csv_path.exists():
        return None
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    if not rows:
        return None
    pps_vals = [int(r["packets_per_second"]) for r in rows]
    total_rx = max(int(r["bytes_received"]) for r in rows) if rows else 0
    return {
        "entries": len(rows),
        "peak_pps": max(pps_vals),
        "avg_pps": sum(pps_vals) / len(pps_vals),
        "total_packets": total_rx,
    }


# ---------------------------------------------------------------------------
# NS-3 runner
# ---------------------------------------------------------------------------
def find_ns3_root() -> Optional[Path]:
    """Find NS-3 installation. Checks common locations and env vars."""
    env = os.environ.get("NS3_BUILD_DIR") or os.environ.get("NS3_ROOT")
    if env:
        p = Path(env)
        if p.name == "build":
            p = p.parent
        if (p / "CMakeLists.txt").exists():
            return p

    candidates = [
        Path.home() / "ns-3.47",
        Path.home() / "ns-3-dev",
        Path.home() / "ns-allinone-3.47" / "ns-3.47",
    ]
    for c in candidates:
        if (c / "CMakeLists.txt").exists():
            return c
    return None


def build_and_run_ns3(
    params: SimParams,
    ns3_root: Path,
    run_tag: str,
) -> Tuple[bool, str]:
    """Build (if needed) and run the NS-3 simulation. Returns (success, message)."""
    scratch_dir = ns3_root / "scratch"
    target_dir = scratch_dir / "RouterHFT"
    sim_file = target_dir / "nic_router_pipeline.cc"

    # Link simulation source into scratch
    target_dir.mkdir(parents=True, exist_ok=True)
    if not sim_file.exists() or sim_file.stat().st_mtime < SIM_SOURCE.stat().st_mtime:
        shutil.copy2(SIM_SOURCE, sim_file)
        print(f"  Copied simulation -> {sim_file}")

    # Build
    print("  Building NS-3 simulation...")
    result = subprocess.run(
        ["./ns3", "build"],
        cwd=str(ns3_root),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        return False, f"Build failed:\n{result.stderr[-2000:]}"

    # Run
    run_args = params.cmdline_args() + [f"--resultsDir={RESULTS_DIR}"]
    print(f"  Running simulation with: {' '.join(run_args)}")
    result = subprocess.run(
        ["./ns3", "run", f"scratch/RouterHFT/nic_router_pipeline", "--", *run_args],
        cwd=str(ns3_root),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        return False, f"Run failed:\n{result.stderr[-2000:]}"

    return True, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Interactive menus
# ---------------------------------------------------------------------------
def list_presets():
    print("\nAvailable presets:")
    print(f"  {'Name':<20} {'Description':<60}")
    print(f"  {'-'*20} {'-'*60}")
    descriptions = {
        "baseline": "Current default (10Gbps, 10us, 50us gap, 256B)",
        "high-throughput": "40Gbps, small packets at 100K pps — stress NIC",
        "long-haul": "100us link delay — simulate geographic distance",
        "congestion-stress": "1Gbps bottleneck with rapid large packets",
        "burst": "MTU-sized 5K packets at 1M pps microburst",
        "hft-co-lo": "100Gbps co-location 1us delay at 1M pps",
    }
    for name, p in PRESETS.items():
        print(f"  {name:<20} {descriptions.get(name, '')}")
        print(f"  {'':<20} {p.summary_line()}")
        print()


def interactive_menu() -> SimParams:
    print(textwrap.dedent("""\
    ╔══════════════════════════════════════════════════════════════╗
    ║          RouterHFT Simulation Parameter Tuner                ║
    ╚══════════════════════════════════════════════════════════════╝
    """))

    # Choose input method
    print("How do you want to configure?")
    print("  1) Use a preset configuration")
    print("  2) Custom (tune each parameter)")
    choice = input("  Enter 1 or 2: ").strip()

    if choice == "1":
        list_presets()
        name = input("  Enter preset name: ").strip().lower()
        if name in PRESETS:
            p = PRESETS[name]
            print(f"\n  Selected preset: {name}")
            print(f"  {p.summary_line()}")
            return p
        else:
            print(f"  Unknown preset '{name}', falling back to custom.")
            choice = "2"

    if choice == "2":
        return custom_param_menu()
    else:
        print("  Defaulting to custom...")
        return custom_param_menu()


def custom_param_menu() -> SimParams:
    p = SimParams()
    print("\n--- Network ---")
    p.link_rate = prompt_enum(
        "Link data rate",
        ["1Gbps", "10Gbps", "40Gbps", "100Gbps"],
        p.link_rate,
    )
    p.link_delay = prompt_enum(
        "Link propagation delay",
        ["1us", "5us", "10us", "50us", "100us", "1ms"],
        p.link_delay,
    )
    print("\n--- Traffic ---")
    p.packet_count = prompt_int("Total packets to send", 100, 10_000_000, p.packet_count)
    p.packet_size = prompt_int("Packet payload size (bytes)", 64, 1500, p.packet_size)
    p.inter_packet_gap_us = prompt_int(
        "Inter-packet gap (microseconds)", 1, 10000, p.inter_packet_gap_us
    )
    print("\n--- Simulation ---")
    p.sim_stop_seconds = prompt_float(
        "Simulation stop time (seconds)", 1.0, 120.0, p.sim_stop_seconds
    )
    print(f"\n  Resulting load: ~{p.pps():.0f} pps, ~{p.data_rate_mbps():.1f} Mbps\n")
    return p


def prompt_enum(label: str, options: List[str], default: str) -> str:
    print(f"  {label}:")
    for i, opt in enumerate(options, 1):
        marker = " [default]" if opt == default else ""
        print(f"    {i}) {opt}{marker}")
    choice = input(f"  Enter number or value (default: {default}): ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            return options[idx]
    if choice in options:
        return choice
    return default


def prompt_int(label: str, lo: int, hi: int, default: int) -> int:
    raw = input(f"  {label} [{lo}-{hi}] (default: {default}): ").strip()
    if raw.isdigit():
        v = int(raw)
        if lo <= v <= hi:
            return v
    return default


def prompt_float(label: str, lo: float, hi: float, default: float) -> float:
    raw = input(f"  {label} [{lo}-{hi}] (default: {default}): ").strip()
    if raw.replace(".", "", 1).isdigit():
        v = float(raw)
        if lo <= v <= hi:
            return v
    return default


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
def generate_plots():
    """Run plot_results.py if matplotlib/pandas are available."""
    plot_script = ROOT / "plot_results.py"
    if not plot_script.exists():
        print("  Plot script not found, skipping visualization.")
        return
    latency_csv = RESULTS_DIR / "latency.csv"
    throughput_csv = RESULTS_DIR / "throughput.csv"
    if not latency_csv.exists() and not throughput_csv.exists():
        print("  No result CSV files found, skipping visualization.")
        return
    print("  Generating plots...")
    result = subprocess.run(
        [sys.executable, str(plot_script),
         str(latency_csv), str(throughput_csv),
         "--output-dir", str(RESULTS_DIR)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        print(f"  Plots saved to {RESULTS_DIR}/")
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                print(f"    {line}")
    else:
        print(f"  Plotting failed (may need matplotlib):\n{result.stderr[-500:]}")


# ---------------------------------------------------------------------------
# Runner logic
# ---------------------------------------------------------------------------
def run_simulation(
    params: SimParams,
    run_tag: str,
    ns3_root: Optional[Path] = None,
    headless: bool = False,
) -> Analysis:
    """Execute a single simulation run and return analysis."""
    RUN_LABEL = f"{run_tag}_{datetime.now():%H%M%S}"

    if not headless:
        print(f"\n{'='*70}")
        print(f"  Run: {RUN_LABEL}")
        print(f"  {params.summary_line()}")
        print(f"{'='*70}\n")

    # Locate NS-3
    if ns3_root is None:
        ns3_root = find_ns3_root()
    if ns3_root is None:
        print("  ERROR: NS-3 installation not found.")
        print("  Set NS3_BUILD_DIR or NS3_ROOT environment variable.")
        return Analysis(name=run_tag, params=params)

    if not headless:
        print(f"  Using NS-3 at: {ns3_root}")

    # Build and run
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    success, output = build_and_run_ns3(params, ns3_root, run_tag)

    if not headless:
        print(f"\n  Simulation output:\n{output[:2000]}")

    if not success:
        print(f"  ERROR: {output}")
        return Analysis(name=run_tag, params=params)

    # Analyze
    latency_csv = RESULTS_DIR / "latency.csv"
    throughput_csv = RESULTS_DIR / "throughput.csv"
    lat_stats = analyze_latency(latency_csv)
    tp_stats = analyze_throughput(throughput_csv)

    analysis = Analysis(
        name=run_tag,
        params=params,
        latency_stats=lat_stats,
        throughput_stats=tp_stats,
        run_dir=RESULTS_DIR,
    )

    if not headless:
        print("\n" + analysis.summary())

    return analysis


def benchmark_mode(presets: List[str], ns3_root: Optional[Path] = None):
    """Run multiple presets sequentially and print comparison."""
    print("\n" + "=" * 70)
    print("  BENCHMARK MODE — Running multiple presets")
    print("=" * 70)

    results: List[Analysis] = []
    for name in presets:
        if name not in PRESETS:
            print(f"\n  Unknown preset '{name}', skipping.")
            continue
        params = PRESETS[name]
        analysis = run_simulation(params, name, ns3_root, headless=False)
        results.append(analysis)

    # Comparison table
    print("\n" + "=" * 70)
    print("  COMPARISON TABLE")
    print("=" * 70)
    header = f"{'Preset':<20} {'Mean Lat':>10} {'P99 Lat':>10} {'Jitter':>10} {'Peak PPS':>10} {'Total Rx':>10}"
    print(header)
    print("-" * 70)
    for r in results:
        ls = r.latency_stats or {}
        ts = r.throughput_stats or {}
        mean_lat = f"{ls.get('mean', 0):>9.0f}ns" if ls else "N/A"
        p99_lat = f"{ls.get('p99', 0):>9.0f}ns" if ls else "N/A"
        jitter = f"{ls.get('jitter_ns', 0):>9.0f}ns" if ls else "N/A"
        peak = f"{ts.get('peak_pps', 0):>10.0f}" if ts else "N/A"
        total = f"{ts.get('total_packets', 0):>10.0f}" if ts else "N/A"
        print(f"{r.name:<20} {mean_lat:>10} {p99_lat:>10} {jitter:>10} {peak:>10} {total:>10}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="RouterHFT Simulation Runner & Parameter Tuner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python3 run_simulation.py                         # Interactive
              python3 run_simulation.py --preset baseline        # Run a single preset
              python3 run_simulation.py --preset baseline,hft-co-lo  # Run multiple
              python3 run_simulation.py --list-presets           # List presets
              python3 run_simulation.py --link-rate 40Gbps --packet-count 100000  # Quick custom
        """),
    )
    parser.add_argument("--preset", help="Preset name(s), comma-separated for benchmark mode")
    parser.add_argument("--list-presets", action="store_true", help="List available presets")
    parser.add_argument("--no-plot", action="store_true", help="Skip plot generation")

    # Quick custom overrides
    parser.add_argument("--link-rate", help="Link data rate (e.g. 1Gbps, 10Gbps, 40Gbps)")
    parser.add_argument("--link-delay", help="Link delay (e.g. 10us, 100us, 1ms)")
    parser.add_argument("--packet-count", type=int, help="Total packets")
    parser.add_argument("--packet-size", type=int, help="Packet size in bytes")
    parser.add_argument("--interval-us", type=int, help="Inter-packet gap in microseconds")
    parser.add_argument("--stop-time", type=float, help="Simulation stop time in seconds")
    parser.add_argument("--ns3-root", help="Path to NS-3 root directory")

    args = parser.parse_args()

    # Resolve NS-3 root
    ns3_root = Path(args.ns3_root) if args.ns3_root else find_ns3_root()
    if ns3_root:
        ns3_root = ns3_root.resolve()

    if args.list_presets:
        list_presets()
        return

    if args.preset:
        presets = [p.strip() for p in args.preset.split(",")]
        if len(presets) > 1:
            benchmark_mode(presets, ns3_root)
        else:
            params = PRESETS.get(presets[0])
            if params is None:
                print(f"Unknown preset '{presets[0]}'")
                return
            # Apply CLI overrides
            params = apply_cli_overrides(params, args)
            run_simulation(params, presets[0], ns3_root, headless=True)
            if not args.no_plot:
                generate_plots()
        return

    # Interactive mode
    params = interactive_menu()

    # Apply CLI overrides (in case user also passed some)
    params = apply_cli_overrides(params, args)

    run_simulation(params, "custom", ns3_root, headless=False)

    if not args.no_plot:
        generate_plots()

    print(f"\n  Results saved to: {RESULTS_DIR}/")
    print(f"  Plot script: python3 {ROOT}/plot_results.py {RESULTS_DIR}/latency.csv {RESULTS_DIR}/throughput.csv")


def apply_cli_overrides(params: SimParams, args) -> SimParams:
    """Apply command-line overrides to a SimParams instance."""
    overrides = {}
    if args.link_rate:
        overrides["link_rate"] = args.link_rate
    if args.link_delay:
        overrides["link_delay"] = args.link_delay
    if args.packet_count:
        overrides["packet_count"] = args.packet_count
    if args.packet_size:
        overrides["packet_size"] = args.packet_size
    if args.interval_us:
        overrides["inter_packet_gap_us"] = args.interval_us
    if args.stop_time:
        overrides["sim_stop_seconds"] = args.stop_time

    if overrides:
        params = SimParams(**{**params.__dict__, **overrides})
    return params


if __name__ == "__main__":
    main()
