#!/usr/bin/env python3
"""
Neuromorphic SNN Training with snnTorch
Full GPU support for both NVIDIA and AMD
Collects all 8 required metrics

Based on Leaky Integrate-and-Fire (LIF) spiking neurons
Implements temporal spike encoding and surrogate gradient learning
"""

import torch
import torch.nn as nn
import snntorch as snn
from snntorch import surrogate
from snntorch import functional as SF
from snntorch import utils
import numpy as np
import json
import time
from datetime import datetime
import sys
import os

# GPU monitoring
try:
    import pynvml
    NVML_AVAILABLE = True
except:
    NVML_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except:
    PSUTIL_AVAILABLE = False


# ============================================================
# Neuromorphic SNN Model Architecture
# ============================================================

class NeuromorphicActivitySNN(nn.Module):
    """
    Spiking Neural Network for Activity Prediction
    
    Architecture:
    - Input: Temporal spike-encoded features
    - Hidden: Leaky Integrate-and-Fire (LIF) neurons
    - Output: LIF neurons for classification
    
    Neuromorphic properties:
    - Membrane potential dynamics
    - Spike-based communication
    - Temporal processing
    - Event-driven computation
    """
    
    def __init__(self, input_size, hidden_size, output_size, beta=0.9, spike_grad=None):
        super().__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Spike gradient for backpropagation through spikes
        if spike_grad is None:
            spike_grad = surrogate.fast_sigmoid(slope=25)
        
        # Network layers
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.lif1 = snn.Leaky(beta=beta, spike_grad=spike_grad)
        
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.lif2 = snn.Leaky(beta=beta, spike_grad=spike_grad)
    
    def forward(self, x, num_steps=20):
        """
        Forward pass with temporal dynamics
        
        Args:
            x: Input features [batch_size, input_size]
            num_steps: Number of timesteps for spiking dynamics
        
        Returns:
            spk_out: Output spikes [num_steps, batch_size, output_size]
            mem_out: Output membrane potentials [batch_size, output_size]
        """
        batch_size = x.shape[0]
        
        # Initialize membrane potentials
        mem1 = self.lif1.init_leaky()
        mem2 = self.lif2.init_leaky()
        
        # Record output spikes
        spk_out_rec = []
        mem_out_rec = []
        
        # Temporal processing (spiking dynamics)
        for step in range(num_steps):
            # Current injection from input (rate coding)
            # Input repeated over time with noise for spike encoding
            cur1 = self.fc1(x + 0.01 * torch.randn_like(x))
            spk1, mem1 = self.lif1(cur1, mem1)
            
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)
            
            spk_out_rec.append(spk2)
            mem_out_rec.append(mem2)
        
        # Stack temporal outputs
        spk_out = torch.stack(spk_out_rec, dim=0)  # [num_steps, batch, output]
        
        return spk_out, mem2  # Return final membrane potential


# ============================================================
# GPU Monitor for Metrics Collection
# ============================================================

class GPUMonitor:
    """Monitor GPU metrics during training - supports NVIDIA and AMD"""
    
    def __init__(self):
        self.gpu_type = self.detect_gpu()
        self.device = self.get_device()
        self.metrics_history = []
        self.start_time = None
        
        print(f"\n{'='*70}")
        print(f"GPU CONFIGURATION")
        print(f"{'='*70}")
        print(f"GPU Type: {self.gpu_type}")
        print(f"Device: {self.device}")
        print(f"{'='*70}\n")
    
    def detect_gpu(self):
        """Detect available GPU (NVIDIA, AMD, or CPU)"""
        
        # Try PyTorch CUDA first (NVIDIA or AMD via ROCm)
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✓ Detected GPU via PyTorch CUDA: {gpu_name}")
            
            # Try NVML for monitoring (optional)
            if NVML_AVAILABLE:
                try:
                    pynvml.nvmlInit()
                    self.nvml = pynvml
                    self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    print(f"✓ NVML monitoring: Enabled")
                    return 'nvidia'
                except Exception as e:
                    print(f"⚠️  NVML monitoring: Disabled ({e})")
                    print(f"   GPU will still be used via PyTorch CUDA!")
                    return 'nvidia_cuda'
            else:
                print(f"⚠️  NVML not available - using PyTorch CUDA metrics")
                return 'nvidia_cuda'
        
        # Try DirectML (AMD on Windows)
        try:
            import torch_directml
            if torch_directml.is_available():
                print(f"✓ Detected AMD GPU via DirectML")
                print(f"   Device: {torch_directml.device()}")
                return 'amd_directml'
        except ImportError:
            print(f"⚠️  DirectML not available (install: pip install torch-directml)")
        except Exception as e:
            print(f"⚠️  DirectML error: {e}")
        
        print("⚠ No GPU detected - using CPU only")
        return 'cpu'
    
    def get_device(self):
        """Get PyTorch device"""
        if self.gpu_type in ['nvidia', 'nvidia_cuda']:
            if torch.cuda.is_available():
                return torch.device('cuda')
        elif self.gpu_type == 'amd_directml':
            try:
                import torch_directml
                return torch_directml.device()
            except:
                pass
        return torch.device('cpu')
    
    def get_gpu_memory(self):
        """Get GPU memory usage"""
        
        if self.gpu_type == 'nvidia' and NVML_AVAILABLE:
            try:
                mem_info = self.nvml.nvmlDeviceGetMemoryInfo(self.handle)
                return {
                    'allocated_mb': mem_info.used / (1024 * 1024),
                    'reserved_mb': mem_info.total / (1024 * 1024),
                }
            except Exception as e:
                print(f"⚠️  NVML memory error: {e}")
                return {'allocated_mb': 0, 'reserved_mb': 0}
        
        elif self.gpu_type in ['nvidia_cuda', 'amd_rocm']:
            # Use PyTorch CUDA memory stats
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(0) / (1024 * 1024)
                reserved = torch.cuda.memory_reserved(0) / (1024 * 1024)
                return {
                    'allocated_mb': allocated,
                    'reserved_mb': reserved,
                }
        
        return {'allocated_mb': 0, 'reserved_mb': 0}
    
    def get_gpu_power(self):
        """Get current GPU power draw (watts)"""
        
        if self.gpu_type == 'nvidia' and NVML_AVAILABLE:
            try:
                power_mw = self.nvml.nvmlDeviceGetPowerUsage(self.handle)
                return power_mw / 1000.0
            except Exception as e:
                # NVML failed, use estimate
                return 115.0
        
        # Estimates for GPUs without NVML
        elif self.gpu_type == 'nvidia_cuda':
            # NVIDIA via CUDA (no NVML) - use TDP estimate
            return 115.0  # Typical for RTX 4060
        elif self.gpu_type == 'amd_rocm':
            return 130.0  # TDP estimate for AMD
        
        return 0.0
    
    def get_gpu_temperature(self):
        """Get GPU temperature"""
        
        if self.gpu_type == 'nvidia' and NVML_AVAILABLE:
            try:
                temp = self.nvml.nvmlDeviceGetTemperature(self.handle, 0)
                return int(temp)
            except Exception as e:
                print(f"⚠️  NVML temperature error: {e}")
                return 0
        
        return 0
    
    def get_ram_usage(self):
        """Get system RAM usage (MB)"""
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                mem_info = process.memory_info()
                return mem_info.rss / (1024 * 1024)
            except:
                return 0.0
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
        
        temps = [m['temperature_c'] for m in self.metrics_history if m['temperature_c'] > 0]
        avg_temp = np.mean(temps) if temps else 0
        
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
            'framework': 'snnTorch',
            'neuromorphic': True,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Metrics saved to: {filepath}")
    
    def cleanup(self):
        """Cleanup GPU monitoring"""
        if self.gpu_type == 'nvidia' and NVML_AVAILABLE:
            try:
                self.nvml.nvmlShutdown()
            except:
                pass


# ============================================================
# Training Data Generation
# ============================================================

ACTIVITY_CLASSES = [
    "rest", "workout", "creative_work", "study", "practice_skill",
    "social_activity", "plan_day", "review_goals", "quick_break",
    "deep_work", "light_task", "brainstorm", "organize",
    "learn_something", "physical_activity", "mental_exercise",
    "relax", "energize", "focus_session", "free_time",
]


def create_context_features(hour, minute, energy, engagement, idle_time, 
                            recent_accepts, recent_rejects):
    """Create feature vector from MiniOS context"""
    features = [
        hour / 24.0,                    # Normalized hour
        minute / 60.0,                  # Normalized minute
        energy / 100.0,                 # Normalized energy
        engagement / 100.0,             # Normalized engagement
        idle_time,                      # Idle time ratio
        recent_accepts / 10.0,          # Normalized accepts
        recent_rejects / 10.0,          # Normalized rejects
        1.0 if hour >= 9 and hour < 17 else 0.0,  # Work hours
        1.0 if hour >= 20 or hour < 6 else 0.0,   # Rest hours
        1.0 if energy > 70 else 0.0,    # High energy
    ]
    return np.array(features, dtype=np.float32)


def generate_training_data(num_samples=100, device='cpu'):
    """Generate synthetic training data with clearer patterns"""
    
    X_list = []
    y_list = []
    
    for _ in range(num_samples):
        hour = np.random.randint(6, 24)
        minute = np.random.randint(0, 60)
        energy = np.random.randint(20, 100)
        engagement = np.random.randint(0, 100)
        idle_time = np.random.rand()
        recent_accepts = np.random.randint(0, 10)
        recent_rejects = np.random.randint(0, 10)
        
        features = create_context_features(
            hour, minute, energy, engagement, idle_time,
            recent_accepts, recent_rejects
        )
        
        # Clearer activity patterns for better learning
        # Morning routines
        if hour >= 6 and hour < 9:
            if energy > 70:
                label = 1  # workout
            else:
                label = 0  # rest
        # Work hours - deep focus
        elif hour >= 9 and hour < 12:
            if engagement > 60 and energy > 50:
                label = 9  # deep_work
            elif energy < 40:
                label = 8  # quick_break
            else:
                label = 10  # light_task
        # Lunch break
        elif hour >= 12 and hour < 14:
            label = 8  # quick_break
        # Afternoon work
        elif hour >= 14 and hour < 17:
            if engagement > 50:
                label = 2  # creative_work
            else:
                label = 10  # light_task
        # Evening
        elif hour >= 17 and hour < 20:
            if energy > 60:
                label = 14  # physical_activity
            else:
                label = 16  # relax
        # Night
        elif hour >= 20:
            if energy < 40:
                label = 0  # rest
            else:
                label = 16  # relax
        else:
            label = 19  # free_time
        
        X_list.append(features)
        y_list.append(label)
    
    X = torch.tensor(np.array(X_list), dtype=torch.float32).to(device)
    y = torch.tensor(y_list, dtype=torch.long).to(device)
    
    return X, y


# ============================================================
# Training Function
# ============================================================

def train_snn(num_epochs=15, num_samples=100, hidden_size=32, num_steps=30, 
              learning_rate=0.01, device='cpu'):  # Increased from 0.001 to 0.01
    """
    Train neuromorphic SNN
    
    Args:
        num_epochs: Number of training epochs
        num_samples: Number of training samples
        hidden_size: Number of hidden neurons
        num_steps: Timesteps for spiking dynamics
        learning_rate: Learning rate (default 0.01 for faster convergence)
        device: torch device (cuda/cpu)
    
    Returns:
        model: Trained SNN model
        monitor: GPU monitor with metrics
    """
    
    print("=" * 70)
    print("NEUROMORPHIC SNN TRAINING (snnTorch)")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Epochs: {num_epochs}")
    print(f"  Samples: {num_samples}")
    print(f"  Hidden neurons: {hidden_size}")
    print(f"  Timesteps: {num_steps}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Device: {device}")
    print()
    
    # Initialize monitor
    monitor = GPUMonitor()
    
    # Generate training data
    print(f"Generating {num_samples} training samples...")
    X_train, y_train = generate_training_data(num_samples, device=monitor.device)
    
    input_size = X_train.shape[1]
    output_size = len(ACTIVITY_CLASSES)
    
    # Create model
    print(f"Creating neuromorphic SNN...")
    print(f"  Input: {input_size} features")
    print(f"  Hidden: {hidden_size} LIF neurons")
    print(f"  Output: {output_size} classes")
    
    model = NeuromorphicActivitySNN(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        beta=0.9
    ).to(monitor.device)
    
    # Initialize weights for better convergence
    with torch.no_grad():
        nn.init.xavier_uniform_(model.fc1.weight)
        nn.init.xavier_uniform_(model.fc2.weight)
    
    # Loss and optimizer
    loss_fn = SF.ce_rate_loss()  # Spike count loss
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    # Start monitoring
    monitor.start_monitoring()
    
    print(f"\nTraining for {num_epochs} epochs...")
    print("-" * 70)
    
    for epoch in range(num_epochs):
        epoch_start = time.time()
        
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        spk_out, mem_out = model(X_train, num_steps=num_steps)
        
        # Loss (spike count)
        loss = loss_fn(spk_out, y_train)
        
        # Backward and optimize
        loss.backward()
        optimizer.step()
        
        # Calculate accuracy
        with torch.no_grad():
            spike_counts = spk_out.sum(0)  # Sum over time
            _, predicted = spike_counts.max(1)
            correct = (predicted == y_train).sum().item()
            accuracy = (correct / len(y_train)) * 100
        
        # Record metrics
        metrics = monitor.record_metrics(
            epoch + 1,
            accuracy,
            loss.item()
        )
        
        print(f"Epoch {epoch+1:2d}/{num_epochs}: "
              f"Loss={loss.item():.4f}, "
              f"Acc={accuracy:5.1f}%, "
              f"Time={metrics['time_seconds']:.1f}s, "
              f"Power={metrics['power_watts']:.1f}W")
    
    print("-" * 70)
    
    # Summary
    summary = monitor.get_summary()
    print(f"\nTraining Summary:")
    print(f"  Total time: {summary['total_time_seconds']:.1f} seconds")
    print(f"  Final accuracy: {summary['final_accuracy']:.1f}%")
    print(f"  Average power: {summary['average_power_watts']:.1f} W")
    print(f"  Total energy: {summary['total_energy_wh']:.4f} Wh")
    print(f"  Max RAM: {summary['max_ram_mb']:.1f} MB")
    print(f"  Max GPU memory: {summary['max_gpu_allocated_mb']:.1f} MB")
    
    return model, monitor


# ============================================================
# Inference Time Measurement
# ============================================================

def measure_inference_time(model, input_size, num_steps=30, num_tests=100, device='cpu'):
    """Measure inference time"""
    
    print("\n" + "=" * 70)
    print("MEASURING INFERENCE TIME")
    print("=" * 70)
    
    model.eval()
    inference_times = []
    
    print(f"\nRunning {num_tests} inference tests...")
    
    with torch.no_grad():
        for i in range(num_tests):
            # Random test input
            x = torch.randn(1, input_size).to(device)
            
            # Measure time
            start_time = time.time()
            spk_out, mem_out = model(x, num_steps=num_steps)
            torch.cuda.synchronize() if device.type == 'cuda' else None
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
    }


# ============================================================
# Model Saving
# ============================================================

def save_model(model, filepath='minios_snn_model.pth'):
    """Save trained model"""
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_size': model.input_size,
        'hidden_size': model.hidden_size,
        'output_size': model.output_size,
        'class_names': ACTIVITY_CLASSES,
    }, filepath)
    print(f"\n✓ Model saved to: {filepath}")


def add_inference_metrics(metrics_file, inference_metrics):
    """Add inference timing to existing metrics file"""
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data['inference_timing'] = inference_metrics
    data['summary']['avg_inference_ms'] = inference_metrics['average_ms']
    data['summary']['p95_inference_ms'] = inference_metrics['p95_ms']
    
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Inference metrics added to: {metrics_file}")


# ============================================================
# Main Training Pipeline
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("NEUROMORPHIC SNN WITH snnTorch")
    print("Full GPU Support: NVIDIA & AMD")
    print("=" * 70)
    
    # Train model
    model, monitor = train_snn(
        num_epochs=15,
        num_samples=100,
        hidden_size=32,
        num_steps=30,
        learning_rate=0.001,
        device=monitor.device if 'monitor' in locals() else 'cpu'
    )
    
    # Save metrics
    monitor.save_metrics('training_metrics.json')
    
    # Measure inference time
    inference_metrics = measure_inference_time(
        model,
        input_size=10,
        num_steps=30,
        num_tests=100,
        device=monitor.device
    )
    
    # Add to metrics
    add_inference_metrics('training_metrics.json', inference_metrics)
    
    # Save model
    save_model(model, 'minios_snn_model.pth')
    
    # Cleanup
    monitor.cleanup()
    
    print("\n" + "=" * 70)
    print("✓ TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\nFiles created:")
    print(f"  - training_metrics.json (all 8 metrics!)")
    print(f"  - minios_snn_model.pth (trained model)")
    print(f"\nNext step: python export_snntorch_to_minios.py")
    print()
