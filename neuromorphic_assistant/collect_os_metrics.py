#!/usr/bin/env python3
"""
Collect and visualize metrics from running MiniOS
Captures data via serial port or log file
"""

import serial
import time
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime
import argparse


class OSMetricsCollector:
    """Collect metrics from running MiniOS"""
    
    def __init__(self, source='serial', port='/dev/ttyS0', logfile='os_metrics.log'):
        self.source = source
        self.port = port
        self.logfile = logfile
        self.serial_conn = None
        self.metrics_history = []
        self.running = False
        
    def connect(self):
        """Connect to data source"""
        
        if self.source == 'serial':
            try:
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=115200,
                    timeout=1
                )
                print(f"✓ Connected to serial port: {self.port}")
                return True
            except Exception as e:
                print(f"✗ Failed to connect to serial: {e}")
                return False
        
        elif self.source == 'file':
            print(f"✓ Monitoring log file: {self.logfile}")
            return True
        
        elif self.source == 'qemu':
            print(f"✓ Monitoring QEMU serial output")
            # QEMU redirects serial to stdio
            return True
        
        return False
    
    def parse_metrics_block(self, text):
        """Parse metrics from text block"""
        
        if 'METRICS_START' not in text or 'METRICS_END' not in text:
            return None
        
        # Extract metrics block
        start = text.index('METRICS_START')
        end = text.index('METRICS_END')
        block = text[start:end]
        
        metrics = {'timestamp': datetime.now().isoformat()}
        
        # Parse key=value pairs
        for line in block.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                try:
                    # Try to parse as number
                    if '.' in value:
                        metrics[key] = float(value)
                    else:
                        metrics[key] = int(value)
                except:
                    metrics[key] = value
        
        return metrics
    
    def collect_from_serial(self):
        """Collect from serial port"""
        
        buffer = ""
        
        while self.running:
            try:
                if self.serial_conn.in_waiting:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    # Check for complete metrics block
                    if 'METRICS_END' in buffer:
                        metrics = self.parse_metrics_block(buffer)
                        if metrics:
                            self.metrics_history.append(metrics)
                            print(f"✓ Collected metrics: {len(self.metrics_history)} samples")
                        buffer = ""
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"✗ Error: {e}")
                time.sleep(1)
    
    def collect_from_file(self):
        """Collect from log file (tail -f style)"""
        
        buffer = ""
        
        with open(self.logfile, 'r') as f:
            # Seek to end
            f.seek(0, 2)
            
            while self.running:
                line = f.readline()
                
                if line:
                    buffer += line
                    
                    if 'METRICS_END' in buffer:
                        metrics = self.parse_metrics_block(buffer)
                        if metrics:
                            self.metrics_history.append(metrics)
                            print(f"✓ Collected metrics: {len(self.metrics_history)} samples")
                        buffer = ""
                else:
                    time.sleep(0.1)
    
    def start_collection(self):
        """Start collecting metrics"""
        
        self.running = True
        
        if self.source == 'serial':
            self.collect_from_serial()
        elif self.source == 'file':
            self.collect_from_file()
    
    def stop_collection(self):
        """Stop collecting"""
        
        self.running = False
        
        if self.serial_conn:
            self.serial_conn.close()
    
    def save_metrics(self, filename='os_runtime_metrics.json'):
        """Save collected metrics to file"""
        
        with open(filename, 'w') as f:
            json.dump({
                'collection_time': datetime.now().isoformat(),
                'num_samples': len(self.metrics_history),
                'data': self.metrics_history
            }, f, indent=2)
        
        print(f"✓ Metrics saved to: {filename}")


def visualize_runtime_metrics(metrics_file='os_runtime_metrics.json', 
                               output_file='os_runtime_graphs.png'):
    """Create comprehensive graphs from collected OS metrics"""
    
    # Load metrics
    with open(metrics_file, 'r') as f:
        data = json.load(f)
    
    history = data['data']
    
    if len(history) == 0:
        print("✗ No metrics to visualize")
        return
    
    # Extract time series data
    timestamps = [i for i in range(len(history))]
    
    accuracy = [m.get('accuracy', 0) for m in history]
    total_inferences = [m.get('total_inferences', 0) for m in history]
    avg_inference_ms = [m.get('avg_inference_ms', 0) for m in history]
    ram_kb = [m.get('ram_current_bytes', 0) / 1024 for m in history]
    gpu_mem_mb = [m.get('gpu_mem_allocated', 0) / (1024*1024) for m in history]
    power_w = [m.get('gpu_power_watts', 0) for m in history]
    energy_mwh = [m.get('energy_mwh', 0) for m in history]
    temp_c = [m.get('gpu_temp_c', 0) for m in history]
    
    # Create visualization
    fig, axes = plt.subplots(3, 3, figsize=(16, 12))
    fig.suptitle('MiniOS Runtime Metrics - Real User Interactions', 
                 fontsize=16, fontweight='bold')
    
    # 1. Accuracy over time
    ax = axes[0, 0]
    ax.plot(timestamps, accuracy, 'b-', linewidth=2, marker='o', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Real-Time Accuracy')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 100])
    
    # 2. Total inferences
    ax = axes[0, 1]
    ax.plot(timestamps, total_inferences, 'g-', linewidth=2, marker='s', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Total Inferences')
    ax.set_title('Cumulative Suggestions')
    ax.grid(True, alpha=0.3)
    
    # 3. Inference time
    ax = axes[0, 2]
    ax.plot(timestamps, avg_inference_ms, 'r-', linewidth=2, marker='^', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Time (ms)')
    ax.set_title('Average Inference Latency')
    ax.grid(True, alpha=0.3)
    
    # 4. RAM usage
    ax = axes[1, 0]
    ax.plot(timestamps, ram_kb, 'purple', linewidth=2, marker='o', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('RAM (KB)')
    ax.set_title('System Memory Usage')
    ax.grid(True, alpha=0.3)
    
    # 5. GPU memory
    ax = axes[1, 1]
    ax.plot(timestamps, gpu_mem_mb, 'c-', linewidth=2, marker='s', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('GPU Memory (MB)')
    ax.set_title('GPU Memory Usage')
    ax.grid(True, alpha=0.3)
    
    # 6. Power consumption
    ax = axes[1, 2]
    ax.plot(timestamps, power_w, 'orange', linewidth=2, marker='^', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Power (W)')
    ax.set_title('GPU Power Draw')
    ax.grid(True, alpha=0.3)
    
    # 7. Energy consumption
    ax = axes[2, 0]
    ax.plot(timestamps, energy_mwh, 'brown', linewidth=2, marker='o', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Energy (mWh)')
    ax.set_title('Cumulative Energy')
    ax.grid(True, alpha=0.3)
    
    # 8. GPU temperature
    ax = axes[2, 1]
    ax.plot(timestamps, temp_c, 'red', linewidth=2, marker='s', markersize=4)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Temperature (°C)')
    ax.set_title('GPU Temperature')
    ax.grid(True, alpha=0.3)
    
    # 9. Summary statistics
    ax = axes[2, 2]
    ax.axis('off')
    
    if len(history) > 0:
        final = history[-1]
        summary_text = f"""
OS RUNTIME SUMMARY
{'='*30}

Total Samples: {len(history)}
Duration: {len(history) * 10} seconds

Final Accuracy: {final.get('accuracy', 0):.1f}%
Total Inferences: {final.get('total_inferences', 0)}

Avg Inference: {final.get('avg_inference_ms', 0)} ms
Min Inference: {final.get('min_inference_ms', 0)} ms
Max Inference: {final.get('max_inference_ms', 0)} ms

Peak RAM: {final.get('ram_peak_bytes', 0) / 1024:.1f} KB
GPU Memory: {final.get('gpu_mem_allocated', 0) / (1024*1024):.1f} MB

Avg Power: {np.mean(power_w):.1f} W
Total Energy: {final.get('energy_mwh', 0):.1f} mWh

Accepts: {final.get('total_accepts', 0)}
Rejects: {final.get('total_rejects', 0)}
"""
        
        ax.text(0.1, 0.9, summary_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Graphs saved to: {output_file}")
    plt.show()


def live_monitor(collector, update_interval=1000):
    """Live visualization while collecting"""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('MiniOS Live Metrics Monitor', fontsize=14, fontweight='bold')
    
    lines = []
    
    # Setup plots
    ax = axes[0, 0]
    line, = ax.plot([], [], 'b-', linewidth=2)
    lines.append(line)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Accuracy')
    ax.set_ylim([0, 100])
    ax.grid(True)
    
    ax = axes[0, 1]
    line, = ax.plot([], [], 'r-', linewidth=2)
    lines.append(line)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Time (ms)')
    ax.set_title('Inference Time')
    ax.grid(True)
    
    ax = axes[1, 0]
    line, = ax.plot([], [], 'g-', linewidth=2)
    lines.append(line)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Power (W)')
    ax.set_title('GPU Power')
    ax.grid(True)
    
    ax = axes[1, 1]
    line, = ax.plot([], [], 'orange', linewidth=2)
    lines.append(line)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Memory (MB)')
    ax.set_title('GPU Memory')
    ax.grid(True)
    
    def update(frame):
        if len(collector.metrics_history) > 0:
            history = collector.metrics_history
            x = list(range(len(history)))
            
            # Update accuracy
            y = [m.get('accuracy', 0) for m in history]
            lines[0].set_data(x, y)
            axes[0, 0].relim()
            axes[0, 0].autoscale_view()
            
            # Update inference time
            y = [m.get('avg_inference_ms', 0) for m in history]
            lines[1].set_data(x, y)
            axes[0, 1].relim()
            axes[0, 1].autoscale_view()
            
            # Update power
            y = [m.get('gpu_power_watts', 0) for m in history]
            lines[2].set_data(x, y)
            axes[1, 0].relim()
            axes[1, 0].autoscale_view()
            
            # Update GPU memory
            y = [m.get('gpu_mem_allocated', 0) / (1024*1024) for m in history]
            lines[3].set_data(x, y)
            axes[1, 1].relim()
            axes[1, 1].autoscale_view()
        
        return lines
    
    ani = FuncAnimation(fig, update, interval=update_interval, blit=True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Collect and visualize MiniOS runtime metrics')
    parser.add_argument('--mode', choices=['collect', 'visualize', 'live'], default='collect',
                       help='Operation mode')
    parser.add_argument('--source', choices=['serial', 'file', 'qemu'], default='file',
                       help='Data source for collection')
    parser.add_argument('--port', default='/dev/ttyS0',
                       help='Serial port (if using serial)')
    parser.add_argument('--logfile', default='os_metrics.log',
                       help='Log file (if using file)')
    parser.add_argument('--output', default='os_runtime_metrics.json',
                       help='Output metrics file')
    parser.add_argument('--graphs', default='os_runtime_graphs.png',
                       help='Output graphs file')
    
    args = parser.parse_args()
    
    if args.mode == 'collect':
        print("\n📊 MiniOS Metrics Collector\n")
        print("Starting collection...")
        print("Press Ctrl+C to stop\n")
        
        collector = OSMetricsCollector(
            source=args.source,
            port=args.port,
            logfile=args.logfile
        )
        
        if collector.connect():
            try:
                collector.start_collection()
            except KeyboardInterrupt:
                print("\n\nStopping collection...")
            finally:
                collector.stop_collection()
                collector.save_metrics(args.output)
                print(f"\n✓ Collected {len(collector.metrics_history)} samples")
    
    elif args.mode == 'visualize':
        print("\n📈 Visualizing collected metrics\n")
        visualize_runtime_metrics(args.output, args.graphs)
    
    elif args.mode == 'live':
        print("\n📺 Starting live monitor\n")
        collector = OSMetricsCollector(source=args.source, port=args.port)
        if collector.connect():
            import threading
            thread = threading.Thread(target=collector.start_collection)
            thread.daemon = True
            thread.start()
            live_monitor(collector)
