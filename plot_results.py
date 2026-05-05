#!/usr/bin/env python3
"""Plot RouterHFT NIC+Router simulation results."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_latency(latency_csv: Path, output_png: Path) -> None:
    df = pd.read_csv(latency_csv)
    if df.empty:
        raise ValueError(f"No rows found in {latency_csv}")

    plt.figure(figsize=(10, 6))
    plt.hist(df["latency_ns"], bins=60, edgecolor="black", alpha=0.8, color="#0f766e")
    plt.title("End-to-End Latency Distribution (NIC -> Router -> Consumer)")
    plt.xlabel("Latency (ns)")
    plt.ylabel("Packet Count")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_png)
    plt.close()


def plot_throughput(throughput_csv: Path, output_png: Path) -> None:
    df = pd.read_csv(throughput_csv)
    if df.empty:
        raise ValueError(f"No rows found in {throughput_csv}")

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(df["second"], df["packets_per_second"], marker="o", color="#1d4ed8", label="Packets/s")
    ax1.set_xlabel("Second")
    ax1.set_ylabel("Packets/s", color="#1d4ed8")
    ax1.tick_params(axis="y", labelcolor="#1d4ed8")

    ax2 = ax1.twinx()
    ax2.plot(df["second"], df["bits_per_second"], marker="s", color="#dc2626", label="Bits/s")
    ax2.set_ylabel("Bits/s", color="#dc2626")
    ax2.tick_params(axis="y", labelcolor="#dc2626")

    ax1.grid(alpha=0.25)
    fig.suptitle("Pipeline Throughput Over Time")
    fig.tight_layout()
    fig.savefig(output_png)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate latency and throughput plots for RouterHFT results.")
    parser.add_argument(
        "latency_csv",
        nargs="?",
        default="results/latency.csv",
        help="Path to latency.csv (default: results/latency.csv)",
    )
    parser.add_argument(
        "throughput_csv",
        nargs="?",
        default="results/throughput.csv",
        help="Path to throughput.csv (default: results/throughput.csv)",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory where PNGs will be written (default: results)",
    )
    args = parser.parse_args()

    latency_csv = Path(args.latency_csv)
    throughput_csv = Path(args.throughput_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    latency_png = output_dir / "latency_histogram.png"
    throughput_png = output_dir / "throughput_timeseries.png"

    plot_latency(latency_csv, latency_png)
    plot_throughput(throughput_csv, throughput_png)

    print(f"Saved {latency_png}")
    print(f"Saved {throughput_png}")


if __name__ == "__main__":
    main()
