#!/usr/bin/env python3
"""
Combine HWiNFO64 GPU metrics with MiniOS runtime metrics
Correlates external GPU monitoring with OS interaction data
"""

import pandas as pd
import json
import numpy as np
from datetime import datetime, timedelta
import argparse
import matplotlib.pyplot as plt


def load_hwinfo_csv(filepath):
    """Load and parse HWiNFO64 CSV log"""
    
    print(f"Loading HWiNFO64 data from: {filepath}")
    
    try:
        # HWiNFO64 CSVs are typically saved in ISO-8859-1 (Latin-1) encoding
        # Try ISO-8859-1 first, then fall back to UTF-8
        
        try:
            df = pd.read_csv(filepath, encoding='iso-8859-1')
            print(f"  ✓ Loaded with ISO-8859-1 encoding")
        except:
            df = pd.read_csv(filepath, encoding='utf-8')
            print(f"  ✓ Loaded with UTF-8 encoding")
        
        print(f"  Found {len(df)} samples")
        print(f"  Columns: {list(df.columns[:5])}...")
        
        return df
        
    except Exception as e:
        print(f"✗ Error loading HWiNFO64 CSV: {e}")
        print(f"\nExpected format:")
        print(f"  - CSV export from HWiNFO64 sensors")
        print(f"  - Columns: Date, Time, GPU Power, GPU Temp, etc.")
        print(f"\nTip: HWiNFO64 typically saves in ISO-8859-1 encoding")
        return None


def extract_gpu_metrics(df):
    """Extract GPU metrics from HWiNFO64 dataframe"""
    
    # First, filter out any header/footer rows
    # HWiNFO64 sometimes repeats headers at the end
    if 'Date' in df.columns:
        valid_rows = df['Date'] != 'Date'
        df = df[valid_rows].copy()
        print(f"  Filtered to {len(df)} data rows")
    
    metrics = {}
    
    # Try to find GPU power column
    power_cols = [col for col in df.columns if 'power' in col.lower() and 'gpu' in col.lower()]
    if power_cols:
        metrics['power'] = pd.to_numeric(df[power_cols[0]], errors='coerce').values
        print(f"  ✓ Found GPU power: {power_cols[0]}")
    else:
        print(f"  ⚠ GPU power column not found")
        metrics['power'] = np.zeros(len(df))
    
    # Try to find GPU temperature
    temp_cols = [col for col in df.columns if 'temp' in col.lower() and 'gpu' in col.lower() and 'hot spot' not in col.lower()]
    if temp_cols:
        metrics['temperature'] = pd.to_numeric(df[temp_cols[0]], errors='coerce').values
        print(f"  ✓ Found GPU temp: {temp_cols[0]}")
    else:
        print(f"  ⚠ GPU temperature column not found")
        metrics['temperature'] = np.zeros(len(df))
    
    # Try to find GPU memory (D3D Memory Dedicated is the allocated memory)
    mem_cols = [col for col in df.columns if 'd3d' in col.lower() and 'dedicated' in col.lower()]
    if not mem_cols:
        mem_cols = [col for col in df.columns if 'memory' in col.lower() and 'gpu' in col.lower() and 'usage' in col.lower()]
    if mem_cols:
        metrics['memory'] = pd.to_numeric(df[mem_cols[0]], errors='coerce').values
        print(f"  ✓ Found GPU memory: {mem_cols[0]}")
    else:
        print(f"  ⚠ GPU memory column not found")
        metrics['memory'] = np.zeros(len(df))
    
    # Parse timestamps
    if 'Time' in df.columns and 'Date' in df.columns:
        try:
            # Filter out header/footer rows that might have been repeated
            # HWiNFO64 sometimes adds headers at the end
            valid_rows = df['Date'] != 'Date'  # Filter out header rows
            df = df[valid_rows].copy()
            
            # Parse timestamps with proper format
            # HWiNFO64 format: DD.MM.YYYY HH:MM:SS.fff
            timestamps = pd.to_datetime(
                df['Date'] + ' ' + df['Time'],
                format='%d.%m.%Y %H:%M:%S.%f',
                errors='coerce'
            )
            
            # Drop any rows where timestamp parsing failed
            valid_timestamps = ~timestamps.isna()
            df = df[valid_timestamps].copy()
            timestamps = timestamps[valid_timestamps]
            
            metrics['timestamps'] = timestamps
            print(f"  ✓ Parsed {len(timestamps)} valid timestamps")
        except Exception as e:
            print(f"  ⚠ Could not parse timestamps: {e}")
            metrics['timestamps'] = None
    elif 'Time' in df.columns:
        timestamps = pd.to_datetime(df['Time'])
        metrics['timestamps'] = timestamps
        print(f"  ✓ Parsed timestamps (time only)")
    else:
        print(f"  ⚠ Timestamp column not found")
        metrics['timestamps'] = None
    
    return metrics


def load_os_metrics(filepath):
    """Load OS runtime metrics JSON"""
    
    print(f"\nLoading OS metrics from: {filepath}")
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        print(f"  ✓ Found {len(data.get('data', []))} OS samples")
        return data
        
    except Exception as e:
        print(f"✗ Error loading OS metrics: {e}")
        return None


def correlate_metrics(hwinfo_metrics, os_data, time_window_seconds=2):
    """Correlate HWiNFO64 and OS metrics by timestamp"""
    
    print(f"\nCorrelating metrics (window: ±{time_window_seconds}s)...")
    
    if hwinfo_metrics['timestamps'] is None:
        print("✗ Cannot correlate without timestamps")
        return None
    
    os_samples = os_data.get('data', [])
    combined = []
    matched = 0
    
    for os_sample in os_samples:
        # Parse OS timestamp
        try:
            os_time = datetime.fromisoformat(os_sample['timestamp'])
        except:
            continue
        
        # Find closest HWiNFO64 sample within time window
        time_diffs = abs(hwinfo_metrics['timestamps'] - os_time)
        min_diff_idx = time_diffs.argmin()
        min_diff_seconds = time_diffs.iloc[min_diff_idx].total_seconds()
        
        if min_diff_seconds <= time_window_seconds:
            # Within window - use this sample
            combined_sample = os_sample.copy()
            
            # Add actual GPU metrics from HWiNFO64
            combined_sample['gpu_power_watts_actual'] = float(hwinfo_metrics['power'][min_diff_idx])
            combined_sample['gpu_temp_c_actual'] = float(hwinfo_metrics['temperature'][min_diff_idx])
            combined_sample['gpu_memory_mb_actual'] = float(hwinfo_metrics['memory'][min_diff_idx])
            combined_sample['hwinfo_timestamp'] = hwinfo_metrics['timestamps'].iloc[min_diff_idx].isoformat()
            combined_sample['time_diff_seconds'] = float(min_diff_seconds)
            
            combined.append(combined_sample)
            matched += 1
        else:
            # Outside window - skip or use estimates
            pass
    
    print(f"  ✓ Matched {matched}/{len(os_samples)} OS samples with HWiNFO64 data")
    
    return combined


def save_combined_metrics(combined, output_file='combined_metrics.json'):
    """Save combined metrics to JSON"""
    
    data = {
        'source': 'combined_hwinfo64_and_os',
        'description': 'OS runtime metrics with actual GPU data from HWiNFO64',
        'num_samples': len(combined),
        'data': combined,
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Combined metrics saved to: {output_file}")
    return output_file


def visualize_combined(combined, output_file='combined_metrics_graph.png'):
    """Create visualization of combined metrics"""
    
    if not combined:
        print("✗ No data to visualize")
        return
    
    # Extract data
    samples = list(range(len(combined)))
    
    # OS metrics
    accuracy = [m.get('accuracy', 0) for m in combined]
    inference_ms = [m.get('avg_inference_ms', 0) for m in combined]
    
    # HWiNFO64 metrics (actual)
    power_actual = [m.get('gpu_power_watts_actual', 0) for m in combined]
    temp_actual = [m.get('gpu_temp_c_actual', 0) for m in combined]
    
    # Create plots
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Combined OS + HWiNFO64 Metrics - AMD GPU', 
                 fontsize=14, fontweight='bold')
    
    # 1. Accuracy
    ax = axes[0, 0]
    ax.plot(samples, accuracy, 'b-', linewidth=2, marker='o', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('OS Learning Accuracy')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 100])
    
    # 2. Inference Time
    ax = axes[0, 1]
    ax.plot(samples, inference_ms, 'g-', linewidth=2, marker='s', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Time (ms)')
    ax.set_title('Inference Latency')
    ax.grid(True, alpha=0.3)
    
    # 3. GPU Power (Actual from HWiNFO64)
    ax = axes[1, 0]
    ax.plot(samples, power_actual, 'r-', linewidth=2, marker='^', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Power (W)')
    ax.set_title('GPU Power (HWiNFO64 Actual)')
    ax.grid(True, alpha=0.3)
    
    # 4. GPU Temperature (Actual from HWiNFO64)
    ax = axes[1, 1]
    ax.plot(samples, temp_actual, 'orange', linewidth=2, marker='o', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Temperature (°C)')
    ax.set_title('GPU Temperature (HWiNFO64 Actual)')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_file}")
    plt.show()


def print_summary(combined):
    """Print summary statistics"""
    
    if not combined:
        return
    
    print("\n" + "=" * 60)
    print("COMBINED METRICS SUMMARY")
    print("=" * 60)
    
    # Extract metrics
    power = [m.get('gpu_power_watts_actual', 0) for m in combined]
    temp = [m.get('gpu_temp_c_actual', 0) for m in combined]
    accuracy = [m.get('accuracy', 0) for m in combined]
    
    print(f"\nGPU Power (Actual from HWiNFO64):")
    print(f"  Average: {np.mean(power):.1f} W")
    print(f"  Min: {np.min(power):.1f} W")
    print(f"  Max: {np.max(power):.1f} W")
    
    print(f"\nGPU Temperature (Actual from HWiNFO64):")
    print(f"  Average: {np.mean(temp):.1f} °C")
    print(f"  Min: {np.min(temp):.1f} °C")
    print(f"  Max: {np.max(temp):.1f} °C")
    
    print(f"\nOS Metrics:")
    print(f"  Final Accuracy: {accuracy[-1]:.1f}%")
    print(f"  Total Samples: {len(combined)}")
    
    # Energy calculation
    if len(combined) > 1:
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in combined]
        duration_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600.0
        energy_wh = np.mean(power) * duration_hours
        
        print(f"\nEnergy Consumption:")
        print(f"  Session duration: {duration_hours * 60:.1f} minutes")
        print(f"  Total energy: {energy_wh:.4f} Wh")
    
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Combine HWiNFO64 GPU metrics with MiniOS runtime metrics'
    )
    parser.add_argument('--hwinfo', default='hwinfo_log.csv',
                       help='HWiNFO64 CSV log file')
    parser.add_argument('--os', default='os_runtime_metrics.json',
                       help='OS runtime metrics JSON file')
    parser.add_argument('--output', default='combined_metrics.json',
                       help='Output combined metrics file')
    parser.add_argument('--graph', default='combined_metrics_graph.png',
                       help='Output graph file')
    parser.add_argument('--window', type=float, default=2.0,
                       help='Time correlation window (seconds)')
    
    args = parser.parse_args()
    
    print("\n📊 Combining HWiNFO64 + MiniOS Metrics\n")
    print("=" * 60)
    
    # Load HWiNFO64 data
    hwinfo_df = load_hwinfo_csv(args.hwinfo)
    if hwinfo_df is None:
        exit(1)
    
    # Extract GPU metrics
    hwinfo_metrics = extract_gpu_metrics(hwinfo_df)
    
    # Load OS metrics
    os_data = load_os_metrics(args.os)
    if os_data is None:
        exit(1)
    
    # Correlate
    combined = correlate_metrics(hwinfo_metrics, os_data, args.window)
    if combined is None or len(combined) == 0:
        print("\n✗ No metrics could be correlated")
        exit(1)
    
    # Save combined
    save_combined_metrics(combined, args.output)
    
    # Print summary
    print_summary(combined)
    
    # Visualize
    visualize_combined(combined, args.graph)
    
    print("\n✓ Complete!")
    print(f"\nFiles created:")
    print(f"  - {args.output} (combined data)")
    print(f"  - {args.graph} (visualization)")
    print()
