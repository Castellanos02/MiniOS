#!/usr/bin/env python3
"""
Analyze HWiNFO64 GPU metrics directly
Works even without OS interaction data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys


def analyze_hwinfo_data(hwinfo_file='session_1.CSV'):
    """Analyze HWiNFO64 CSV data"""
    
    print("\n📊 Analyzing HWiNFO64 GPU Metrics\n")
    print("=" * 60)
    
    try:
        # Load data with proper encoding (HWiNFO64 uses ISO-8859-1)
        try:
            df = pd.read_csv(hwinfo_file, encoding='iso-8859-1')
        except:
            df = pd.read_csv(hwinfo_file, encoding='utf-8')
        
        print(f"✓ Loaded {len(df)} samples from {hwinfo_file}")
        print(f"  Duration: {len(df)} seconds ({len(df)/60:.1f} minutes)")
        
    except FileNotFoundError:
        print(f"✗ File not found: {hwinfo_file}")
        print("  Make sure the file is in the current directory")
        return
    except Exception as e:
        print(f"✗ Error loading file: {e}")
        return
    
    print("\n" + "=" * 60)
    print("GPU METRICS SUMMARY")
    print("=" * 60)
    
    # Power metrics
    if 'GPU PPT [W]' in df.columns:
        power_ppt = df['GPU PPT [W]']
        print(f"\nGPU Power (PPT):")
        print(f"  Average: {power_ppt.mean():.2f} W")
        print(f"  Minimum: {power_ppt.min():.2f} W")
        print(f"  Maximum: {power_ppt.max():.2f} W")
        print(f"  Std Dev: {power_ppt.std():.2f} W")
    
    if 'GPU ASIC Power [W]' in df.columns:
        power_asic = df['GPU ASIC Power [W]']
        print(f"\nGPU Power (ASIC):")
        print(f"  Average: {power_asic.mean():.2f} W")
        print(f"  Minimum: {power_asic.min():.2f} W")
        print(f"  Maximum: {power_asic.max():.2f} W")
    
    # Temperature
    if 'GPU Temperature [°C]' in df.columns:
        temp = df['GPU Temperature [°C]']
        print(f"\nGPU Temperature:")
        print(f"  Average: {temp.mean():.1f} °C")
        print(f"  Minimum: {temp.min():.1f} °C")
        print(f"  Maximum: {temp.max():.1f} °C")
    
    if 'GPU Hot Spot Temperature [°C]' in df.columns:
        hotspot = df['GPU Hot Spot Temperature [°C]']
        print(f"\nGPU Hot Spot:")
        print(f"  Average: {hotspot.mean():.1f} °C")
        print(f"  Maximum: {hotspot.max():.1f} °C")
    
    # Memory
    if 'GPU D3D Memory Dedicated [MB]' in df.columns:
        mem_dedicated = df['GPU D3D Memory Dedicated [MB]']
        print(f"\nGPU Memory (Allocated):")
        print(f"  Average: {mem_dedicated.mean():.1f} MB")
        print(f"  Minimum: {mem_dedicated.min():.1f} MB")
        print(f"  Maximum: {mem_dedicated.max():.1f} MB")
    
    if 'GPU Memory Usage [MB]' in df.columns:
        mem_usage = df['GPU Memory Usage [MB]']
        print(f"\nGPU Memory (Total):")
        print(f"  Average: {mem_usage.mean():.1f} MB")
        print(f"  Minimum: {mem_usage.min():.1f} MB")
        print(f"  Maximum: {mem_usage.max():.1f} MB")
    
    # Clocks
    if 'GPU Clock [MHz]' in df.columns:
        clock = df['GPU Clock [MHz]']
        print(f"\nGPU Core Clock:")
        print(f"  Average: {clock.mean():.1f} MHz")
        print(f"  Maximum: {clock.max():.1f} MHz")
    
    if 'GPU Memory Clock [MHz]' in df.columns:
        mem_clock = df['GPU Memory Clock [MHz]']
        print(f"\nGPU Memory Clock:")
        print(f"  Average: {mem_clock.mean():.1f} MHz")
    
    # Energy calculation
    if 'GPU PPT [W]' in df.columns:
        duration_hours = len(df) / 3600.0  # 1 sample per second
        avg_power = df['GPU PPT [W]'].mean()
        total_energy_wh = avg_power * duration_hours
        
        print("\n" + "=" * 60)
        print("ENERGY ANALYSIS")
        print("=" * 60)
        print(f"\nSession Duration: {len(df)} seconds ({len(df)/60:.1f} minutes)")
        print(f"Average Power: {avg_power:.2f} W")
        print(f"Total Energy: {total_energy_wh:.4f} Wh")
        print(f"Total Energy: {total_energy_wh * 1000:.2f} mWh")
    
    print("\n" + "=" * 60)
    
    # Create visualization
    create_hwinfo_graphs(df)
    
    return df


def create_hwinfo_graphs(df, output_file='hwinfo_gpu_analysis.png'):
    """Create comprehensive GPU metrics visualization"""
    
    fig, axes = plt.subplots(3, 3, figsize=(16, 12))
    fig.suptitle('AMD GPU Metrics - HWiNFO64 Data', fontsize=16, fontweight='bold')
    
    samples = list(range(len(df)))
    
    # 1. GPU Power (PPT)
    if 'GPU PPT [W]' in df.columns:
        ax = axes[0, 0]
        ax.plot(samples, df['GPU PPT [W]'], 'b-', linewidth=1)
        ax.set_xlabel('Sample')
        ax.set_ylabel('Power (W)')
        ax.set_title('GPU Power (PPT)')
        ax.grid(True, alpha=0.3)
    
    # 2. GPU Temperature
    if 'GPU Temperature [°C]' in df.columns:
        ax = axes[0, 1]
        ax.plot(samples, df['GPU Temperature [°C]'], 'r-', linewidth=1)
        ax.set_xlabel('Sample')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('GPU Temperature')
        ax.grid(True, alpha=0.3)
    
    # 3. GPU Hot Spot
    if 'GPU Hot Spot Temperature [°C]' in df.columns:
        ax = axes[0, 2]
        ax.plot(samples, df['GPU Hot Spot Temperature [°C]'], 'orange', linewidth=1)
        ax.set_xlabel('Sample')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('GPU Hot Spot Temperature')
        ax.grid(True, alpha=0.3)
    
    # 4. GPU Memory Dedicated
    if 'GPU D3D Memory Dedicated [MB]' in df.columns:
        ax = axes[1, 0]
        ax.plot(samples, df['GPU D3D Memory Dedicated [MB]'], 'g-', linewidth=1)
        ax.set_xlabel('Sample')
        ax.set_ylabel('Memory (MB)')
        ax.set_title('GPU Memory Allocated')
        ax.grid(True, alpha=0.3)
    
    # 5. GPU Memory Usage
    if 'GPU Memory Usage [MB]' in df.columns:
        ax = axes[1, 1]
        ax.plot(samples, df['GPU Memory Usage [MB]'], 'c-', linewidth=1)
        ax.set_xlabel('Sample')
        ax.set_ylabel('Memory (MB)')
        ax.set_title('GPU Memory Total')
        ax.grid(True, alpha=0.3)
    
    # 6. GPU Core Clock
    if 'GPU Clock [MHz]' in df.columns:
        ax = axes[1, 2]
        ax.plot(samples, df['GPU Clock [MHz]'], 'purple', linewidth=1)
        ax.set_xlabel('Sample')
        ax.set_ylabel('Clock (MHz)')
        ax.set_title('GPU Core Clock')
        ax.grid(True, alpha=0.3)
    
    # 7. GPU Memory Clock
    if 'GPU Memory Clock [MHz]' in df.columns:
        ax = axes[2, 0]
        ax.plot(samples, df['GPU Memory Clock [MHz]'], 'brown', linewidth=1)
        ax.set_xlabel('Sample')
        ax.set_ylabel('Clock (MHz)')
        ax.set_title('GPU Memory Clock')
        ax.grid(True, alpha=0.3)
    
    # 8. Power vs Temperature
    if 'GPU PPT [W]' in df.columns and 'GPU Temperature [°C]' in df.columns:
        ax = axes[2, 1]
        ax.scatter(df['GPU PPT [W]'], df['GPU Temperature [°C]'], alpha=0.5, s=10)
        ax.set_xlabel('Power (W)')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('Power vs Temperature')
        ax.grid(True, alpha=0.3)
    
    # 9. Summary statistics
    ax = axes[2, 2]
    ax.axis('off')
    
    summary_text = f"""
GPU METRICS SUMMARY
{'='*30}

Samples: {len(df)}
Duration: {len(df)/60:.1f} minutes

Power (PPT):
  Avg: {df['GPU PPT [W]'].mean():.1f} W
  Max: {df['GPU PPT [W]'].max():.1f} W

Temperature:
  Avg: {df['GPU Temperature [°C]'].mean():.1f} °C
  Max: {df['GPU Temperature [°C]'].max():.1f} °C

Memory (Allocated):
  Avg: {df['GPU D3D Memory Dedicated [MB]'].mean():.0f} MB

Memory (Total):
  Avg: {df['GPU Memory Usage [MB]'].mean():.0f} MB

Energy:
  Total: {(df['GPU PPT [W]'].mean() * len(df) / 3600):.4f} Wh
"""
    
    ax.text(0.1, 0.9, summary_text, transform=ax.transAxes,
           fontsize=9, verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Graph saved to: {output_file}")


if __name__ == "__main__":
    import sys
    
    # Get filename from command line or use default
    if len(sys.argv) > 1:
        hwinfo_file = sys.argv[1]
    else:
        hwinfo_file = 'session_1.CSV'
    
    # Analyze
    df = analyze_hwinfo_data(hwinfo_file)
    
    if df is not None:
        print("\n✓ Analysis complete!")
        print(f"  Graph: hwinfo_gpu_analysis.png")
        print(f"\nYou have 5 of your 8 required metrics:")
        print("  ✅ GPU Allocated Memory (from HWiNFO64)")
        print("  ✅ GPU Reserved Memory (from HWiNFO64)")
        print("  ✅ Power (from HWiNFO64)")
        print("  ✅ Watt-hours (calculated)")
        print("  ✅ Total Time (from sample count)")
        print("\n  Missing (require OS interaction):")
        print("  ❌ Accuracy")
        print("  ❌ RAM")
        print("  ❌ Inference Time")
