#!/usr/bin/env python3
"""
Visualize GPU Training Metrics
Creates comprehensive graphs from collected data
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

def load_metrics(training_file='training_metrics.json', inference_file='inference_metrics.json'):
    """Load metrics from JSON files"""
    
    with open(training_file, 'r') as f:
        training_data = json.load(f)
    
    try:
        with open(inference_file, 'r') as f:
            inference_data = json.load(f)
    except:
        inference_data = None
    
    return training_data, inference_data


def plot_all_metrics(training_data, inference_data=None, output_file='snn_metrics.png'):
    """Create comprehensive visualization of all metrics"""
    
    history = training_data['history']
    summary = training_data['summary']
    
    # Extract data
    epochs = [m['epoch'] for m in history]
    accuracy = [m['accuracy'] for m in history]
    loss = [m['loss'] for m in history]
    time_s = [m['time_seconds'] for m in history]
    ram_mb = [m['ram_mb'] for m in history]
    gpu_alloc_mb = [m['gpu_allocated_mb'] for m in history]
    gpu_reserved_mb = [m['gpu_reserved_mb'] for m in history]
    power_w = [m['power_watts'] for m in history]
    energy_wh = [m['energy_wh'] for m in history]
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # 1. Accuracy over time
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(epochs, accuracy, 'b-', linewidth=2, marker='o')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy (%)')
    ax1.set_title('Training Accuracy Over Time')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 100])
    
    # 2. Loss over time
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(epochs, loss, 'r-', linewidth=2, marker='o')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.set_title('Training Loss Over Time')
    ax2.grid(True, alpha=0.3)
    
    # 3. RAM Usage
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(epochs, ram_mb, 'g-', linewidth=2, marker='s')
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('RAM (MB)')
    ax3.set_title('System RAM Usage')
    ax3.grid(True, alpha=0.3)
    
    # 4. GPU Memory (Allocated vs Reserved)
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.plot(epochs, gpu_alloc_mb, 'c-', linewidth=2, marker='o', label='Allocated')
    ax4.plot(epochs, gpu_reserved_mb, 'm--', linewidth=2, marker='s', label='Reserved')
    ax4.set_xlabel('Epoch')
    ax4.set_ylabel('GPU Memory (MB)')
    ax4.set_title('GPU Memory Usage')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Power Consumption
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.plot(epochs, power_w, 'orange', linewidth=2, marker='o')
    ax5.set_xlabel('Epoch')
    ax5.set_ylabel('Power (Watts)')
    ax5.set_title('GPU Power Consumption')
    ax5.grid(True, alpha=0.3)
    
    # 6. Cumulative Energy
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.plot(epochs, energy_wh, 'brown', linewidth=2, marker='o')
    ax6.set_xlabel('Epoch')
    ax6.set_ylabel('Energy (Wh)')
    ax6.set_title('Cumulative Energy Consumption')
    ax6.grid(True, alpha=0.3)
    
    # 7. Training Time
    ax7 = fig.add_subplot(gs[2, 0])
    ax7.plot(epochs, time_s, 'purple', linewidth=2, marker='o')
    ax7.set_xlabel('Epoch')
    ax7.set_ylabel('Time (seconds)')
    ax7.set_title('Cumulative Training Time')
    ax7.grid(True, alpha=0.3)
    
    # 8. Inference Time Distribution (if available)
    if inference_data:
        ax8 = fig.add_subplot(gs[2, 1])
        inf_times = inference_data['all_times_ms']
        ax8.hist(inf_times, bins=30, color='teal', alpha=0.7, edgecolor='black')
        ax8.axvline(inference_data['average_ms'], color='red', linestyle='--', 
                   linewidth=2, label=f"Avg: {inference_data['average_ms']:.2f} ms")
        ax8.set_xlabel('Inference Time (ms)')
        ax8.set_ylabel('Frequency')
        ax8.set_title('Inference Time Distribution')
        ax8.legend()
        ax8.grid(True, alpha=0.3)
    
    # 9. Summary Statistics
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')
    
    summary_text = f"""
TRAINING SUMMARY
{'='*30}

GPU Type: {training_data['gpu_type'].upper()}

Final Accuracy: {summary['final_accuracy']:.1f}%

Total Time: {summary['total_time_seconds']:.1f} s
Total Energy: {summary['total_energy_wh']:.4f} Wh

Avg Power: {summary['average_power_watts']:.1f} W
Peak RAM: {summary['max_ram_mb']:.1f} MB
Peak GPU Mem: {summary['max_gpu_allocated_mb']:.1f} MB
"""
    
    if inference_data:
        summary_text += f"""
Avg Inference: {inference_data['average_ms']:.2f} ms
Min Inference: {inference_data['min_ms']:.2f} ms
Max Inference: {inference_data['max_ms']:.2f} ms
"""
    
    ax9.text(0.1, 0.9, summary_text, transform=ax9.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Overall title
    fig.suptitle('SNN Training Metrics - GPU Accelerated', fontsize=16, fontweight='bold')
    
    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Graphs saved to: {output_file}")
    
    plt.show()


def create_comparison_plots(nvidia_file, amd_file, output_file='gpu_comparison.png'):
    """Compare NVIDIA vs AMD performance"""
    
    try:
        with open(nvidia_file, 'r') as f:
            nvidia_data = json.load(f)
    except:
        print(f"⚠ Could not load {nvidia_file}")
        nvidia_data = None
    
    try:
        with open(amd_file, 'r') as f:
            amd_data = json.load(f)
    except:
        print(f"⚠ Could not load {amd_file}")
        amd_data = None
    
    if not nvidia_data and not amd_data:
        print("⚠ No data available for comparison")
        return
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('NVIDIA RTX 4060 vs AMD RX 5500 XT - Performance Comparison', 
                 fontsize=14, fontweight='bold')
    
    metrics = [
        ('final_accuracy', 'Final Accuracy (%)', 0),
        ('total_time_seconds', 'Total Time (s)', 1),
        ('total_energy_wh', 'Total Energy (Wh)', 2),
        ('average_power_watts', 'Avg Power (W)', 3),
        ('max_ram_mb', 'Peak RAM (MB)', 4),
        ('max_gpu_allocated_mb', 'Peak GPU Memory (MB)', 5),
    ]
    
    for metric, title, idx in metrics:
        ax = axes[idx // 3, idx % 3]
        
        values = []
        labels = []
        colors = []
        
        if nvidia_data and metric in nvidia_data['summary']:
            values.append(nvidia_data['summary'][metric])
            labels.append('NVIDIA\nRTX 4060')
            colors.append('green')
        
        if amd_data and metric in amd_data['summary']:
            values.append(amd_data['summary'][metric])
            labels.append('AMD\nRX 5500 XT')
            colors.append('red')
        
        if values:
            bars = ax.bar(labels, values, color=colors, alpha=0.7, edgecolor='black')
            ax.set_ylabel(title)
            ax.set_title(title)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}',
                       ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Comparison saved to: {output_file}")
    plt.show()


def export_to_csv(training_data, output_file='training_metrics.csv'):
    """Export metrics to CSV for external analysis"""
    
    import csv
    
    history = training_data['history']
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = history[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in history:
            writer.writerow(row)
    
    print(f"✓ CSV exported to: {output_file}")


if __name__ == "__main__":
    print("\n📊 Visualizing SNN Training Metrics\n")
    
    # Load metrics
    try:
        training_data, inference_data = load_metrics()
        
        # Create comprehensive plots
        plot_all_metrics(training_data, inference_data, 'snn_training_metrics.png')
        
        # Export to CSV
        export_to_csv(training_data, 'training_metrics.csv')
        
        print("\n✓ Visualization complete!")
        print("  - Graphs: snn_training_metrics.png")
        print("  - CSV: training_metrics.csv")
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print("\nMake sure you've run train_with_gpu_metrics.py first!")
    
    # Optional: Compare GPUs if you have both datasets
    # create_comparison_plots('nvidia_metrics.json', 'amd_metrics.json', 'gpu_comparison.png')
