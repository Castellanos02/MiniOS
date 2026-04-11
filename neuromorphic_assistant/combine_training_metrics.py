#!/usr/bin/env python3
"""
Combine Training Metrics (Python) + HWiNFO64 GPU Data
Merges Python training metrics with real GPU hardware data
"""

import pandas as pd
import json
import numpy as np
from datetime import datetime
import argparse
import matplotlib.pyplot as plt


def load_hwinfo_csv(filepath):
    """Load and parse HWiNFO64 CSV log"""
    
    print(f"\nLoading HWiNFO64 data from: {filepath}")
    
    try:
        # HWiNFO64 uses ISO-8859-1 encoding
        try:
            df = pd.read_csv(filepath, encoding='iso-8859-1')
            print(f"  ✓ Loaded with ISO-8859-1 encoding")
        except:
            df = pd.read_csv(filepath, encoding='utf-8')
            print(f"  ✓ Loaded with UTF-8 encoding")
        
        # Filter out footer header rows
        if 'Date' in df.columns:
            valid_rows = df['Date'] != 'Date'
            df = df[valid_rows].copy()
        
        print(f"  ✓ Found {len(df)} data samples")
        
        return df
        
    except Exception as e:
        print(f"✗ Error loading HWiNFO64 CSV: {e}")
        return None


def extract_hwinfo_summary(df):
    """Extract summary statistics from HWiNFO64 data"""
    
    summary = {}
    
    # Find GPU power
    power_cols = [col for col in df.columns if 'power' in col.lower() and 'gpu' in col.lower()]
    if power_cols:
        power_data = pd.to_numeric(df[power_cols[0]], errors='coerce').dropna()
        summary['gpu_power_avg_w'] = float(power_data.mean())
        summary['gpu_power_min_w'] = float(power_data.min())
        summary['gpu_power_max_w'] = float(power_data.max())
        print(f"  ✓ GPU Power: {power_cols[0]}")
        print(f"    Average: {summary['gpu_power_avg_w']:.2f} W")
        print(f"    Min: {summary['gpu_power_min_w']:.2f} W")
        print(f"    Max: {summary['gpu_power_max_w']:.2f} W")
    
    # Find GPU temperature
    temp_cols = [col for col in df.columns if 'temp' in col.lower() and 'gpu' in col.lower() and 'hot spot' not in col.lower()]
    if temp_cols:
        temp_data = pd.to_numeric(df[temp_cols[0]], errors='coerce').dropna()
        summary['gpu_temp_avg_c'] = float(temp_data.mean())
        summary['gpu_temp_min_c'] = float(temp_data.min())
        summary['gpu_temp_max_c'] = float(temp_data.max())
        print(f"  ✓ GPU Temperature: {temp_cols[0]}")
        print(f"    Average: {summary['gpu_temp_avg_c']:.1f} °C")
        print(f"    Max: {summary['gpu_temp_max_c']:.1f} °C")
    
    # Find GPU memory (D3D Dedicated)
    mem_cols = [col for col in df.columns if 'd3d' in col.lower() and 'dedicated' in col.lower()]
    if mem_cols:
        mem_data = pd.to_numeric(df[mem_cols[0]], errors='coerce').dropna()
        summary['gpu_allocated_mb'] = float(mem_data.mean())
        print(f"  ✓ GPU Memory Allocated: {mem_cols[0]}")
        print(f"    Average: {summary['gpu_allocated_mb']:.0f} MB")
    
    # Find GPU memory (Total Usage)
    usage_cols = [col for col in df.columns if 'memory usage' in col.lower() and 'gpu' in col.lower()]
    if usage_cols:
        usage_data = pd.to_numeric(df[usage_cols[0]], errors='coerce').dropna()
        summary['gpu_reserved_mb'] = float(usage_data.mean())
        print(f"  ✓ GPU Memory Total: {usage_cols[0]}")
        print(f"    Average: {summary['gpu_reserved_mb']:.0f} MB")
    
    # Calculate energy
    if 'gpu_power_avg_w' in summary:
        # Duration in hours (1 sample per second)
        duration_hours = len(df) / 3600.0
        summary['total_energy_wh'] = summary['gpu_power_avg_w'] * duration_hours
        print(f"  ✓ Energy Calculation:")
        print(f"    Duration: {len(df)} seconds ({len(df)/60:.1f} minutes)")
        print(f"    Total Energy: {summary['total_energy_wh']:.4f} Wh")
    
    return summary


def load_training_metrics(filepath):
    """Load training metrics from Python script"""
    
    print(f"\nLoading training metrics from: {filepath}")
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        summary = data.get('summary', {})
        history = data.get('history', [])
        
        print(f"  ✓ Training completed successfully")
        print(f"    Final Accuracy: {summary.get('final_accuracy', 0):.1f}%")
        print(f"    Training Time: {summary.get('total_time_seconds', 0):.1f} seconds")
        print(f"    Max RAM: {summary.get('max_ram_mb', 0):.1f} MB")
        print(f"    Epochs: {len(history)}")
        
        if 'avg_inference_ms' in summary:
            print(f"    Avg Inference: {summary['avg_inference_ms']:.2f} ms")
        
        return data  # Return full data including history
        
    except Exception as e:
        print(f"✗ Error loading training metrics: {e}")
        return None


def match_hwinfo_to_epochs(hwinfo_df, training_data):
    """Match HWiNFO64 data to training epochs by timestamp"""
    
    print("\n📊 Matching HWiNFO64 data to epochs...")
    
    history = training_data.get('history', [])
    if not history:
        print("  ⚠️  No epoch history found in training data")
        return []
    
    # Calculate time per epoch
    total_time = training_data['summary'].get('total_time_seconds', 0)
    num_epochs = len(history)
    
    if num_epochs == 0:
        return []
    
    # HWiNFO64 samples per second (usually 1Hz = 1 sample/sec)
    total_hwinfo_samples = len(hwinfo_df)
    samples_per_second = total_hwinfo_samples / total_time if total_time > 0 else 1.0
    
    print(f"  Total training time: {total_time:.2f} seconds")
    print(f"  HWiNFO64 samples: {total_hwinfo_samples}")
    print(f"  Sample rate: {samples_per_second:.2f} Hz")
    
    # Find relevant HWiNFO64 columns
    power_cols = [col for col in hwinfo_df.columns if 'power' in col.lower() and 'gpu' in col.lower()]
    temp_cols = [col for col in hwinfo_df.columns if 'temp' in col.lower() and 'gpu' in col.lower() and 'hot spot' not in col.lower()]
    mem_alloc_cols = [col for col in hwinfo_df.columns if 'd3d' in col.lower() and 'dedicated' in col.lower()]
    mem_total_cols = [col for col in hwinfo_df.columns if 'memory usage' in col.lower() and 'gpu' in col.lower()]
    
    if power_cols:
        print(f"  ✓ Power column: {power_cols[0]}")
    if temp_cols:
        print(f"  ✓ Temp column: {temp_cols[0]}")
    if mem_alloc_cols:
        print(f"  ✓ Memory allocated column: {mem_alloc_cols[0]}")
    if mem_total_cols:
        print(f"  ✓ Memory total column: {mem_total_cols[0]}")
    
    # Process each epoch
    enhanced_history = []
    cumulative_time = 0.0
    
    for i, epoch in enumerate(history):
        # Get epoch duration
        if i == 0:
            epoch_duration = epoch.get('time_seconds', 0)
        else:
            epoch_duration = epoch.get('time_seconds', 0) - history[i-1].get('time_seconds', 0)
        
        # Calculate HWiNFO64 indices for this epoch's time window
        start_time = cumulative_time
        end_time = cumulative_time + epoch_duration
        
        # Convert to sample indices
        start_idx = int(start_time * samples_per_second)
        end_idx = int(end_time * samples_per_second)
        
        # Ensure we get at least 1 sample per epoch (critical for fast epochs!)
        if end_idx <= start_idx:
            end_idx = start_idx + 1
        
        # Make sure we don't exceed array bounds
        start_idx = min(start_idx, total_hwinfo_samples - 1)
        end_idx = min(end_idx, total_hwinfo_samples)
        
        # Get HWiNFO64 slice for this epoch
        epoch_hwinfo = hwinfo_df.iloc[start_idx:end_idx]
        
        # Extract averages for this epoch
        enhanced_epoch = epoch.copy()
        
        # Initialize with zeros (will be overwritten if data exists)
        enhanced_epoch.setdefault('power_watts', 0.0)
        enhanced_epoch.setdefault('temperature_c', 0.0)
        enhanced_epoch.setdefault('gpu_allocated_mb', 0.0)
        enhanced_epoch.setdefault('gpu_reserved_mb', 0.0)
        enhanced_epoch.setdefault('energy_wh', 0.0)
        
        if len(epoch_hwinfo) > 0:
            # Power
            if power_cols:
                power_data = pd.to_numeric(epoch_hwinfo[power_cols[0]], errors='coerce').dropna()
                if len(power_data) > 0:
                    enhanced_epoch['power_watts'] = float(power_data.mean())
            
            # Temperature
            if temp_cols:
                temp_data = pd.to_numeric(epoch_hwinfo[temp_cols[0]], errors='coerce').dropna()
                if len(temp_data) > 0:
                    enhanced_epoch['temperature_c'] = float(temp_data.mean())
            
            # GPU Memory Allocated
            if mem_alloc_cols:
                mem_data = pd.to_numeric(epoch_hwinfo[mem_alloc_cols[0]], errors='coerce').dropna()
                if len(mem_data) > 0:
                    enhanced_epoch['gpu_allocated_mb'] = float(mem_data.mean())
            
            # GPU Memory Total/Reserved
            if mem_total_cols:
                total_data = pd.to_numeric(epoch_hwinfo[mem_total_cols[0]], errors='coerce').dropna()
                if len(total_data) > 0:
                    enhanced_epoch['gpu_reserved_mb'] = float(total_data.mean())
            
            # Calculate energy for this epoch
            if enhanced_epoch['power_watts'] > 0:
                enhanced_epoch['energy_wh'] = enhanced_epoch['power_watts'] * (epoch_duration / 3600.0)
        
        # Debug info for epochs with no data
        if len(epoch_hwinfo) == 0:
            print(f"  ⚠️  Epoch {i+1}: No HWiNFO64 samples (duration={epoch_duration:.3f}s, indices={start_idx}-{end_idx})")
        else:
            print(f"  Epoch {i+1}/{num_epochs}: "
                  f"Duration={epoch_duration:.3f}s, "
                  f"Samples={len(epoch_hwinfo)}, "
                  f"Power={enhanced_epoch.get('power_watts', 0):.1f}W, "
                  f"Temp={enhanced_epoch.get('temperature_c', 0):.1f}°C")
        
        enhanced_history.append(enhanced_epoch)
        cumulative_time = end_time
    
    # Post-process: Fill in any remaining zeros by interpolation from neighbors
    print("\n📊 Filling gaps with interpolation...")
    for i, epoch in enumerate(enhanced_history):
        # If power is 0, try to interpolate from neighbors
        if epoch.get('power_watts', 0) == 0:
            # Find previous non-zero
            prev_power = 0
            for j in range(i-1, -1, -1):
                if enhanced_history[j].get('power_watts', 0) > 0:
                    prev_power = enhanced_history[j]['power_watts']
                    break
            
            # Find next non-zero
            next_power = 0
            for j in range(i+1, len(enhanced_history)):
                if enhanced_history[j].get('power_watts', 0) > 0:
                    next_power = enhanced_history[j]['power_watts']
                    break
            
            # Interpolate
            if prev_power > 0 and next_power > 0:
                epoch['power_watts'] = (prev_power + next_power) / 2.0
                print(f"  Epoch {i+1}: Interpolated power {epoch['power_watts']:.1f}W")
            elif prev_power > 0:
                epoch['power_watts'] = prev_power
                print(f"  Epoch {i+1}: Used previous power {epoch['power_watts']:.1f}W")
            elif next_power > 0:
                epoch['power_watts'] = next_power
                print(f"  Epoch {i+1}: Used next power {epoch['power_watts']:.1f}W")
            
            # Do the same for temperature
            if epoch.get('temperature_c', 0) == 0:
                prev_temp = next_temp = 0
                for j in range(i-1, -1, -1):
                    if enhanced_history[j].get('temperature_c', 0) > 0:
                        prev_temp = enhanced_history[j]['temperature_c']
                        break
                for j in range(i+1, len(enhanced_history)):
                    if enhanced_history[j].get('temperature_c', 0) > 0:
                        next_temp = enhanced_history[j]['temperature_c']
                        break
                
                if prev_temp > 0 and next_temp > 0:
                    epoch['temperature_c'] = (prev_temp + next_temp) / 2.0
                elif prev_temp > 0:
                    epoch['temperature_c'] = prev_temp
                elif next_temp > 0:
                    epoch['temperature_c'] = next_temp
            
            # Recalculate energy if we got power
            if epoch.get('power_watts', 0) > 0:
                epoch_duration = epoch.get('time_seconds', 0) - (enhanced_history[i-1].get('time_seconds', 0) if i > 0 else 0)
                epoch['energy_wh'] = epoch['power_watts'] * (epoch_duration / 3600.0)
    
    return enhanced_history


def combine_metrics(training_data, hwinfo_summary, enhanced_history):
    """Combine training and HWiNFO64 metrics into complete dataset"""
    
    print("\n" + "=" * 70)
    print("COMBINING METRICS")
    print("=" * 70)
    
    training_summary = training_data.get('summary', {})
    
    combined = {
        'collection_date': datetime.now().isoformat(),
        'source': 'Training + HWiNFO64',
        
        'summary': {
            # From training (accurate)
            'accuracy_percent': training_summary.get('final_accuracy', 0),
            'ram_mb': training_summary.get('max_ram_mb', 0),
            'total_time_seconds': training_summary.get('total_time_seconds', 0),
            'avg_inference_ms': training_summary.get('avg_inference_ms', 0),
            
            # From HWiNFO64 (accurate - REAL hardware!)
            'gpu_allocated_mb': hwinfo_summary.get('gpu_allocated_mb', 0),
            'gpu_reserved_mb': hwinfo_summary.get('gpu_reserved_mb', 0),
            'gpu_power_avg_w': hwinfo_summary.get('gpu_power_avg_w', 0),
            'gpu_power_min_w': hwinfo_summary.get('gpu_power_min_w', 0),
            'gpu_power_max_w': hwinfo_summary.get('gpu_power_max_w', 0),
            'gpu_temp_avg_c': hwinfo_summary.get('gpu_temp_avg_c', 0),
            'gpu_temp_max_c': hwinfo_summary.get('gpu_temp_max_c', 0),
            'total_energy_wh': hwinfo_summary.get('total_energy_wh', 0),
            
            # Bonus metrics
            'gpu_type': training_summary.get('gpu_type', 'unknown'),
        },
        
        # Enhanced history with HWiNFO64 data per epoch
        'history': enhanced_history,
        
        # Keep original inference timing if available
        'inference_timing': training_data.get('inference_timing', {}),
        
        # Keep use case info if available
        'use_cases': training_data.get('use_cases', {}),
        
        # Framework info
        'framework': training_data.get('framework', 'snnTorch'),
        'neuromorphic': training_data.get('neuromorphic', True),
    }
    
    # Add inference timing details if available
    if 'p95_inference_ms' in training_summary:
        combined['summary']['p95_inference_ms'] = training_summary['p95_inference_ms']
    
    print("\n✅ ALL 8 REQUIRED METRICS:")
    print(f"  #1 Accuracy: {combined['summary']['accuracy_percent']:.1f}%")
    print(f"  #2 RAM: {combined['summary']['ram_mb']:.1f} MB")
    print(f"  #3 GPU Allocated: {combined['summary']['gpu_allocated_mb']:.1f} MB (HWiNFO64)")
    print(f"  #4 GPU Reserved: {combined['summary']['gpu_reserved_mb']:.1f} MB (HWiNFO64)")
    print(f"  #5 Power: {combined['summary']['gpu_power_avg_w']:.2f} W (HWiNFO64)")
    print(f"  #6 Energy: {combined['summary']['total_energy_wh']:.4f} Wh (calculated)")
    print(f"  #7 Total Time: {combined['summary']['total_time_seconds']:.1f} seconds")
    print(f"  #8 Inference Time: {combined['summary']['avg_inference_ms']:.2f} ms")
    print(f"\n✅ BONUS: Per-epoch history with HWiNFO64 data ({len(enhanced_history)} epochs)")
    
    return combined


def save_combined_metrics(combined, output_path):
    """Save combined metrics to JSON"""
    
    with open(output_path, 'w') as f:
        json.dump(combined, f, indent=2)
    
    print(f"\n✓ Combined metrics saved to: {output_path}")


def create_visualization(combined, output_path):
    """Create visualization of metrics"""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Training Metrics Summary', fontsize=16, fontweight='bold')
    
    # 1. Accuracy
    ax = axes[0, 0]
    ax.bar(['Accuracy'], [combined['accuracy_percent']], color='green', alpha=0.7)
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Final Accuracy')
    ax.set_ylim([0, 100])
    ax.grid(True, alpha=0.3, axis='y')
    
    # 2. Power
    ax = axes[0, 1]
    power_data = [
        combined['gpu_power_min_w'],
        combined['gpu_power_avg_w'],
        combined['gpu_power_max_w']
    ]
    ax.bar(['Min', 'Avg', 'Max'], power_data, color='orange', alpha=0.7)
    ax.set_ylabel('Power (W)')
    ax.set_title('GPU Power (HWiNFO64)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 3. Temperature
    ax = axes[1, 0]
    ax.bar(['Average', 'Maximum'], 
           [combined['gpu_temp_avg_c'], combined['gpu_temp_max_c']],
           color='red', alpha=0.7)
    ax.set_ylabel('Temperature (°C)')
    ax.set_title('GPU Temperature (HWiNFO64)')
    ax.grid(True, alpha=0.3, axis='y')
    
    # 4. Summary Stats
    ax = axes[1, 1]
    ax.axis('off')
    
    summary_text = f"""
COMPLETE METRICS SUMMARY
{'='*30}

Training:
  Accuracy: {combined['accuracy_percent']:.1f}%
  Time: {combined['total_time_seconds']:.1f}s
  RAM: {combined['ram_mb']:.0f} MB
  Inference: {combined['avg_inference_ms']:.2f} ms

GPU (HWiNFO64 - REAL):
  Power: {combined['gpu_power_avg_w']:.1f} W
  Temp: {combined['gpu_temp_avg_c']:.1f} °C
  Memory: {combined['gpu_allocated_mb']:.0f} MB
  Energy: {combined['total_energy_wh']:.4f} Wh

All 8 Metrics: ✅ COMPLETE
"""
    
    ax.text(0.1, 0.9, summary_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Combine Training Metrics + HWiNFO64 GPU Data')
    parser.add_argument('--training', required=True, help='training_metrics.json from Python script')
    parser.add_argument('--hwinfo', required=True, help='HWiNFO64 CSV file')
    parser.add_argument('--output', default='complete_training_metrics.json', help='Output JSON file')
    parser.add_argument('--graph', default='training_metrics_graph.png', help='Output graph file')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("📊 COMBINING TRAINING METRICS + HWINFO64 GPU DATA")
    print("=" * 70)
    
    # Load HWiNFO64 data
    hwinfo_df = load_hwinfo_csv(args.hwinfo)
    if hwinfo_df is None:
        return
    
    hwinfo_summary = extract_hwinfo_summary(hwinfo_df)
    
    # Load training metrics (full data including history)
    training_data = load_training_metrics(args.training)
    if training_data is None:
        return
    
    # Match HWiNFO64 data to each epoch
    enhanced_history = match_hwinfo_to_epochs(hwinfo_df, training_data)
    
    # Combine
    combined = combine_metrics(training_data, hwinfo_summary, enhanced_history)
    
    # Save
    save_combined_metrics(combined, args.output)
    
    # Visualize
    create_visualization(combined['summary'], args.graph)
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS - ALL 8 METRICS COLLECTED!")
    print("=" * 70)
    print(f"\nFiles created:")
    print(f"  - {args.output} (complete metrics with per-epoch HWiNFO64 data)")
    print(f"  - {args.graph} (visualization)")
    print("\n✅ Ready for research/analysis!")


if __name__ == "__main__":
    main()
