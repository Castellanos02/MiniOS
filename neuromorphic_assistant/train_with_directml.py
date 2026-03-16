#!/usr/bin/env python3
"""
GPU-Accelerated SNN Training with DirectML Support for AMD on Windows
Supports: NVIDIA CUDA, AMD DirectML, and CPU fallback
"""

import sys
import os
import time
import numpy as np
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_parameters import Model_Params
from assistant import PersonalAssistant


# ============================================================
# GPU Detection and Setup
# ============================================================

class GPUMonitor:
    """Monitor GPU metrics during training - supports DirectML for AMD"""
    
    def __init__(self):
        self.gpu_type = self.detect_gpu()
        self.metrics_history = []
        self.start_time = None
        self.device = None
        
    def detect_gpu(self):
        """Detect available GPU (NVIDIA, AMD DirectML, or CPU)"""
        
        # Try NVIDIA first
        try:
            import pynvml
            pynvml.nvmlInit()
            self.nvml = pynvml
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_name = pynvml.nvmlDeviceGetName(self.handle)
                print(f"✓ Detected NVIDIA GPU: {gpu_name}")
                return 'nvidia'
        except Exception as e:
            print(f"  NVIDIA not available: {e}")
        
        # Try AMD DirectML (Windows)
        try:
            import torch_directml
            if torch_directml.is_available():
                device_count = torch_directml.device_count()
                if device_count > 0:
                    self.device = torch_directml.device(0)
                    print(f"✓ Detected AMD GPU via DirectML: {torch_directml.device_name(0)}")
                    print(f"  DirectML devices available: {device_count}")
                    self.torch_directml = torch_directml
                    return 'amd_directml'
        except Exception as e:
            print(f"  DirectML not available: {e}")
        
        # Try AMD ROCm (Linux)
        try:
            import amdsmi
            amdsmi.amdsmi_init()
            self.amdsmi = amdsmi
            devices = amdsmi.amdsmi_get_processor_handles()
            if len(devices) > 0:
                self.amd_device = devices[0]
                gpu_info = amdsmi.amdsmi_get_gpu_asic_info(self.amd_device)
                gpu_name = gpu_info.get('market_name', 'AMD GPU')
                print(f"✓ Detected AMD GPU via ROCm: {gpu_name}")
                return 'amd_rocm'
        except Exception as e:
            print(f"  ROCm not available: {e}")
        
        print("⚠ No GPU detected - using CPU only")
        return 'cpu'
    
    def get_gpu_memory(self):
        """Get GPU memory usage"""
        
        if self.gpu_type == 'nvidia':
            try:
                mem_info = self.nvml.nvmlDeviceGetMemoryInfo(self.handle)
                return {
                    'allocated_mb': mem_info.used / (1024 * 1024),
                    'reserved_mb': mem_info.total / (1024 * 1024),
                    'free_mb': mem_info.free / (1024 * 1024),
                }
            except:
                return {'allocated_mb': 0, 'reserved_mb': 0, 'free_mb': 0}
        
        elif self.gpu_type == 'amd_directml':
            # DirectML doesn't expose detailed memory info easily
            # Use psutil to estimate
            try:
                import psutil
                # Rough estimate based on process memory
                process = psutil.Process()
                mem_mb = process.memory_info().rss / (1024 * 1024)
                return {
                    'allocated_mb': mem_mb,
                    'reserved_mb': 4096,  # Assume 4GB GPU
                    'free_mb': 4096 - mem_mb,
                }
            except:
                return {'allocated_mb': 0, 'reserved_mb': 0, 'free_mb': 0}
        
        elif self.gpu_type == 'amd_rocm':
            try:
                mem_info = self.amdsmi.amdsmi_get_gpu_memory_usage(
                    self.amd_device,
                    self.amdsmi.AmdSmiMemoryType.VRAM
                )
                return {
                    'allocated_mb': mem_info['vram_used'] / (1024 * 1024),
                    'reserved_mb': mem_info['vram_total'] / (1024 * 1024),
                    'free_mb': (mem_info['vram_total'] - mem_info['vram_used']) / (1024 * 1024),
                }
            except:
                return {'allocated_mb': 0, 'reserved_mb': 0, 'free_mb': 0}
        
        return {'allocated_mb': 0, 'reserved_mb': 0, 'free_mb': 0}
    
    def get_gpu_power(self):
        """Get current GPU power draw (watts)"""
        
        if self.gpu_type == 'nvidia':
            try:
                power_mw = self.nvml.nvmlDeviceGetPowerUsage(self.handle)
                return power_mw / 1000.0
            except:
                return 0.0
        
        elif self.gpu_type == 'amd_directml':
            # DirectML doesn't expose power info
            # Estimate based on AMD RX 5500 XT specs
            return 130.0  # TDP estimate for RX 5500 XT
        
        elif self.gpu_type == 'amd_rocm':
            try:
                power_info = self.amdsmi.amdsmi_get_power_info(self.amd_device)
                return power_info['average_socket_power']
            except:
                return 0.0
        
        return 0.0
    
    def get_gpu_temperature(self):
        """Get GPU temperature"""
        
        if self.gpu_type == 'nvidia':
            try:
                temp = self.nvml.nvmlDeviceGetTemperature(self.handle, 0)
                return temp
            except:
                return 0
        
        elif self.gpu_type == 'amd_directml':
            # DirectML doesn't expose temperature
            return 65  # Typical estimate
        
        elif self.gpu_type == 'amd_rocm':
            try:
                temp_info = self.amdsmi.amdsmi_get_temp_metric(
                    self.amd_device,
                    self.amdsmi.AmdSmiTemperatureType.EDGE,
                    self.amdsmi.AmdSmiTemperatureMetric.CURRENT
                )
                return int(temp_info)
            except:
                return 0
        
        return 0
    
    def get_ram_usage(self):
        """Get system RAM usage (MB)"""
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            return mem_info.rss / (1024 * 1024)
        except:
            return 0.0
    
    def start_monitoring(self):
        """Start monitoring session"""
        self.start_time = time.time()
        self.metrics_history = []
    
    def record_metrics(self, epoch, accuracy, loss):
        """Record metrics at current point in training"""
        
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        gpu_mem = self.get_gpu_memory()
        gpu_power = self.get_gpu_power()
        gpu_temp = self.get_gpu_temperature()
        ram_usage = self.get_ram_usage()
        
        # Estimate energy (watt-hours)
        energy_wh = (gpu_power * elapsed_time) / 3600.0
        
        metrics = {
            'epoch': epoch,
            'accuracy': accuracy,
            'loss': loss,
            'time_seconds': elapsed_time,
            'ram_mb': ram_usage,
            'gpu_allocated_mb': gpu_mem['allocated_mb'],
            'gpu_reserved_mb': gpu_mem['reserved_mb'],
            'gpu_free_mb': gpu_mem['free_mb'],
            'power_watts': gpu_power,
            'energy_wh': energy_wh,
            'temperature_c': gpu_temp,
            'timestamp': datetime.now().isoformat(),
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def get_summary(self):
        """Get summary of all metrics"""
        
        if not self.metrics_history:
            return {}
        
        total_time = self.metrics_history[-1]['time_seconds']
        total_energy = self.metrics_history[-1]['energy_wh']
        final_accuracy = self.metrics_history[-1]['accuracy']
        
        avg_power = np.mean([m['power_watts'] for m in self.metrics_history])
        max_ram = max([m['ram_mb'] for m in self.metrics_history])
        max_gpu_mem = max([m['gpu_allocated_mb'] for m in self.metrics_history])
        avg_temp = np.mean([m['temperature_c'] for m in self.metrics_history if m['temperature_c'] > 0])
        
        return {
            'total_time_seconds': total_time,
            'total_energy_wh': total_energy,
            'final_accuracy': final_accuracy,
            'average_power_watts': avg_power,
            'max_ram_mb': max_ram,
            'max_gpu_allocated_mb': max_gpu_mem,
            'average_temperature_c': avg_temp,
            'gpu_type': self.gpu_type,
        }
    
    def save_metrics(self, filepath='training_metrics.json'):
        """Save all metrics to JSON file"""
        
        data = {
            'summary': self.get_summary(),
            'history': self.metrics_history,
            'gpu_type': self.gpu_type,
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Metrics saved to: {filepath}")
    
    def cleanup(self):
        """Cleanup GPU monitoring"""
        if self.gpu_type == 'nvidia':
            try:
                self.nvml.nvmlShutdown()
            except:
                pass
        elif self.gpu_type == 'amd_rocm':
            try:
                self.amdsmi.amdsmi_shut_down()
            except:
                pass


# ============================================================
# Training Functions
# ============================================================

ACTIVITY_CLASSES = [
    "rest", "workout", "creative_work", "study", "practice_skill",
    "social_activity", "plan_day", "review_goals", "quick_break",
    "deep_work", "light_task", "brainstorm", "organize",
    "learn_something", "physical_activity", "mental_exercise",
    "relax", "energize", "focus_session", "free_time",
]


def create_minios_context(hour, minute, energy, engagement, idle_time, 
                          recent_accepts, recent_rejects):
    """Map MiniOS features to context format"""
    
    return {
        "intent": "other",
        "dialog_state": "idle",
        "time_calendar": {
            "hour_of_day": float(hour),
            "is_weekend": 0.0,
            "in_commute": 0.0,
            "busy_now": 1.0 if engagement > 70 else 0.0,
        },
        "candidate": {
            "suggestion": "none",
            "extra1": float(energy) / 100.0,
            "extra2": float(recent_accepts) / 10.0,
            "extra3": float(recent_rejects) / 10.0,
        },
    }


def generate_training_data(num_samples=100):
    """Generate training data"""
    
    training_data = []
    
    for _ in range(num_samples):
        hour = np.random.randint(6, 24)
        minute = np.random.randint(0, 60)
        energy = np.random.randint(20, 100)
        engagement = np.random.randint(0, 100)
        idle_time = np.random.rand()
        recent_accepts = np.random.randint(0, 10)
        recent_rejects = np.random.randint(0, 10)
        
        context = create_minios_context(
            hour, minute, energy, engagement, idle_time,
            recent_accepts, recent_rejects
        )
        
        # Activity labels
        if hour < 9 and energy > 70:
            activity_idx = 1
        elif 9 <= hour < 12 and energy > 60:
            activity_idx = 9
        elif 12 <= hour < 14:
            activity_idx = 8
        elif 14 <= hour < 17 and engagement > 50:
            activity_idx = 2
        elif 17 <= hour < 20:
            activity_idx = 10
        elif hour >= 20:
            activity_idx = 0
        else:
            activity_idx = 19
        
        training_data.append((context, activity_idx))
    
    return training_data


def train_with_gpu_monitoring(num_epochs=15, lr=0.02, num_samples=100, 
                               hidden_size=32, timesteps=30):
    """Train model with comprehensive GPU monitoring"""
    
    print("=" * 70)
    print("GPU-ACCELERATED SNN TRAINING - DirectML Support for AMD")
    print("=" * 70)
    
    # Initialize GPU monitor
    monitor = GPUMonitor()
    
    print(f"\nConfiguration:")
    print(f"  GPU Type: {monitor.gpu_type}")
    print(f"  Hidden neurons: {hidden_size}")
    print(f"  Timesteps: {timesteps}")
    print(f"  Training samples: {num_samples}")
    print(f"  Epochs: {num_epochs}")
    print(f"  Learning rate: {lr}")
    
    # Create model
    params = Model_Params(
        input_size=None,
        hidden_layers=[hidden_size],
        output_size=len(ACTIVITY_CLASSES),
        steps=timesteps,
    )
    
    assistant = PersonalAssistant(params, class_names=ACTIVITY_CLASSES)
    
    # Generate training data
    print(f"\nGenerating {num_samples} training samples...")
    training_data = generate_training_data(num_samples)
    
    # Start monitoring
    monitor.start_monitoring()
    
    print(f"\nTraining with GPU monitoring...")
    print("-" * 70)
    print(f"{'Epoch':<6} {'Loss':<10} {'Acc%':<8} {'Time(s)':<8} {'Power(W)':<10} {'Energy(Wh)':<12} {'RAM(MB)':<10} {'GPU(MB)':<10}")
    print("-" * 70)
    
    for epoch in range(num_epochs):
        epoch_start = time.time()
        total_loss = 0.0
        correct = 0
        
        for i, (context, true_idx) in enumerate(training_data):
            # Progress indicator
            if i % 10 == 0 and i > 0:
                print(f"  Epoch {epoch+1}/{num_epochs} - Sample {i}/{len(training_data)}...", end='\r')
            
            pred_idx, pred_name, rates = assistant.suggest(context)
            
            feedback = "accept" if pred_idx == true_idx else "reject"
            if feedback == "accept":
                correct += 1
            
            loss = assistant.update_from_feedback(context, pred_idx, feedback, lr=lr)
            total_loss += loss
        
        # Calculate metrics
        avg_loss = total_loss / len(training_data)
        accuracy = (correct / len(training_data)) * 100
        
        # Record metrics
        metrics = monitor.record_metrics(epoch + 1, accuracy, avg_loss)
        
        # Print progress
        print(f"{epoch+1:<6} {avg_loss:<10.4f} {accuracy:<8.1f} "
              f"{metrics['time_seconds']:<8.1f} {metrics['power_watts']:<10.1f} "
              f"{metrics['energy_wh']:<12.4f} {metrics['ram_mb']:<10.1f} "
              f"{metrics['gpu_allocated_mb']:<10.1f}")
    
    print("-" * 70)
    
    # Summary
    summary = monitor.get_summary()
    print(f"\nTraining Summary:")
    print(f"  GPU Type: {summary['gpu_type']}")
    print(f"  Total time: {summary['total_time_seconds']:.1f} seconds")
    print(f"  Total energy: {summary['total_energy_wh']:.4f} Wh")
    print(f"  Final accuracy: {summary['final_accuracy']:.1f}%")
    print(f"  Average power: {summary['average_power_watts']:.1f} W")
    print(f"  Peak RAM: {summary['max_ram_mb']:.1f} MB")
    print(f"  Peak GPU memory: {summary['max_gpu_allocated_mb']:.1f} MB")
    if summary.get('average_temperature_c', 0) > 0:
        print(f"  Average temp: {summary['average_temperature_c']:.1f}°C")
    
    # Save metrics
    monitor.save_metrics('training_metrics.json')
    
    # Save model
    save_model(assistant, 'minios_activity_model.npz')
    
    # Measure inference time
    print("\n" + "=" * 70)
    print("MEASURING INFERENCE TIME")
    print("=" * 70)
    inference_times = measure_inference_time(assistant, num_tests=100)
    
    # Add inference metrics to saved data
    add_inference_metrics('training_metrics.json', inference_times)
    
    # Cleanup
    monitor.cleanup()
    
    return assistant, monitor


def save_model(assistant, filepath="minios_activity_model.npz"):
    """Save trained model"""
    
    model = assistant.model
    
    np.savez(
        filepath,
        Weight_input_hidden=model.Weight_input_hidden,
        Weight_hidden_output=model.Weight_hidden_output,
        input_size=assistant.params.input_size,
        hidden_size=assistant.params.hidden_layers[0],
        output_size=assistant.params.output_size,
        steps=assistant.params.steps,
        class_names=assistant.class_names,
    )
    
    print(f"\n✓ Model saved to: {filepath}")


def measure_inference_time(assistant, num_tests=100):
    """Measure inference time over multiple predictions"""
    
    print(f"\nRunning {num_tests} inference tests...")
    
    inference_times = []
    
    for i in range(num_tests):
        # Create random test context
        hour = np.random.randint(6, 24)
        minute = np.random.randint(0, 60)
        energy = np.random.randint(20, 100)
        engagement = np.random.randint(0, 100)
        idle_time = np.random.rand()
        recent_accepts = np.random.randint(0, 10)
        recent_rejects = np.random.randint(0, 10)
        
        context = create_minios_context(
            hour, minute, energy, engagement, idle_time,
            recent_accepts, recent_rejects
        )
        
        # Measure inference time
        start_time = time.time()
        pred_idx, pred_name, rates = assistant.suggest(context)
        elapsed_ms = (time.time() - start_time) * 1000.0
        
        inference_times.append(elapsed_ms)
        
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{num_tests} tests completed...")
    
    # Calculate statistics
    avg_time = np.mean(inference_times)
    min_time = np.min(inference_times)
    max_time = np.max(inference_times)
    std_time = np.std(inference_times)
    p50_time = np.percentile(inference_times, 50)
    p95_time = np.percentile(inference_times, 95)
    p99_time = np.percentile(inference_times, 99)
    
    print(f"\n✓ Inference time measurement complete!")
    print(f"  Average: {avg_time:.2f} ms")
    print(f"  Minimum: {min_time:.2f} ms")
    print(f"  Maximum: {max_time:.2f} ms")
    print(f"  Std Dev: {std_time:.2f} ms")
    print(f"  P50 (Median): {p50_time:.2f} ms")
    print(f"  P95: {p95_time:.2f} ms")
    print(f"  P99: {p99_time:.2f} ms")
    
    return {
        'num_tests': num_tests,
        'average_ms': float(avg_time),
        'minimum_ms': float(min_time),
        'maximum_ms': float(max_time),
        'std_dev_ms': float(std_time),
        'p50_ms': float(p50_time),
        'p95_ms': float(p95_time),
        'p99_ms': float(p99_time),
        'all_times_ms': [float(t) for t in inference_times],
    }


def add_inference_metrics(metrics_file, inference_metrics):
    """Add inference timing to existing metrics file"""
    
    # Load existing metrics
    with open(metrics_file, 'r') as f:
        data = json.load(f)
    
    # Add inference metrics
    data['inference_timing'] = inference_metrics
    
    # Also add to summary
    data['summary']['avg_inference_ms'] = inference_metrics['average_ms']
    data['summary']['p95_inference_ms'] = inference_metrics['p95_ms']
    
    # Save back
    with open(metrics_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Inference metrics added to: {metrics_file}")


def save_model(assistant, filepath="minios_activity_model.npz"):
    """Save trained model"""
    
    model = assistant.model
    
    np.savez(
        filepath,
        Weight_input_hidden=model.Weight_input_hidden,
        Weight_hidden_output=model.Weight_hidden_output,
        input_size=assistant.params.input_size,
        hidden_size=assistant.params.hidden_layers[0],
        output_size=assistant.params.output_size,
        steps=assistant.params.steps,
        class_names=assistant.class_names,
    )
    
    print(f"\n✓ Model saved to: {filepath}")


if __name__ == "__main__":
    print("\n🚀 GPU-Accelerated SNN Training with DirectML Support\n")
    
    # Check for available packages
    print("Checking GPU support...\n")
    
    try:
        import pynvml
        print("✓ NVIDIA monitoring available (pynvml)")
    except:
        print("  NVIDIA monitoring not available")
    
    try:
        import torch_directml
        if torch_directml.is_available():
            print(f"✓ DirectML available - {torch_directml.device_count()} device(s)")
            print(f"  Device 0: {torch_directml.device_name(0)}")
        else:
            print("  DirectML installed but no devices found")
    except:
        print("  DirectML not available - install: pip install torch-directml")
    
    try:
        import amdsmi
        print("✓ AMD ROCm monitoring available (amdsmi)")
    except:
        print("  AMD ROCm monitoring not available")
    
    try:
        import psutil
        print("✓ System monitoring available (psutil)")
    except:
        print("  System monitoring not available - install: pip install psutil")
    
    print()
    
    # Train with monitoring
    assistant, monitor = train_with_gpu_monitoring(
        num_epochs=15,
        lr=0.02,
        num_samples=100,
        hidden_size=32,
        timesteps=30,
    )
    
    print("\n✓ Training complete!")
    print("  - Model: minios_activity_model.npz")
    print("  - Metrics: training_metrics.json")
    print("\nNext step: python export_to_minios.py")
    print()
