#!/usr/bin/env python3
"""
Train Neuromorphic SNN on Real Use Cases
With default preferences and proactive suggestions

Features:
- Fills idle time proactively (not just reactive)
- Learns from accept/reject feedback
- Context-aware suggestions
- Default preferences that adapt
"""

import torch
import torch.nn as nn
import snntorch as snn
from snntorch import surrogate
from snntorch import functional as SF
import numpy as np
import json
import time
from datetime import datetime

# ── Spike visualisation (optional) ──────────────────────────────────────────
try:
    from visualize_spikes import SpikeVisualizer, ACTIVITY_LABELS as VIZ_LABELS
    VIZ_AVAILABLE = True
    _viz = SpikeVisualizer(output_dir="spike_plots")
    print("✓ SpikeVisualizer loaded  →  plots will be saved to ./spike_plots/")
except ImportError:
    VIZ_AVAILABLE = False
    print("⚠  visualize_spikes.py not found — spike plots disabled")

# Epochs at which to save a full raster+rate dashboard (0 = every epoch)
PLOT_EPOCHS = {1, 5, 10, 15, 20}   # adjust as needed
# Set to None to plot every epoch:  PLOT_EPOCHS = None

# Import use case data
from use_case_data import (
    generate_use_case_training_data,
    ACTIVITY_LABELS,
    UserProfile,
    USE_CASES
)

# Try to import psutil for RAM monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available - RAM monitoring disabled")

# Try to import NVML for NVIDIA GPU monitoring
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False


# ============================================================
# Neuromorphic SNN Model
# ============================================================

class NeuromorphicActivitySNN(nn.Module):
    """
    Spiking Neural Network for activity suggestion
    Uses Leaky Integrate-and-Fire (LIF) neurons with surrogate gradients
    """
    
    def __init__(self, input_size=10, hidden_size=64, output_size=20, beta=0.9):
        super().__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Surrogate gradient for backpropagation through spikes
        spike_grad = surrogate.fast_sigmoid(slope=25)
        
        # Layers with surrogate gradients (manual hidden state management)
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.lif1 = snn.Leaky(beta=beta, spike_grad=spike_grad)
        
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.lif2 = snn.Leaky(beta=beta, spike_grad=spike_grad)
    
    def forward(self, x, num_steps=20):
        """
        Forward pass through spiking network
        
        Args:
            x: Input tensor (batch_size, input_size)
            num_steps: Number of time steps for spiking
            
        Returns:
            spk_out: Output spikes (num_steps, batch_size, output_size)
            mem_out: Output membrane potential
        """
        batch_size = x.shape[0]
        
        # Initialize hidden states
        mem1 = self.lif1.init_leaky()
        mem2 = self.lif2.init_leaky()
        
        # Record spikes at both layers
        spk_hidden_rec = []
        spk_out_rec = []

        # Process through time
        for step in range(num_steps):
            # Input -> Hidden
            cur1 = self.fc1(x)
            spk1, mem1 = self.lif1(cur1, mem1)
            spk_hidden_rec.append(spk1)

            # Hidden -> Output
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)

            spk_out_rec.append(spk2)

        # Stack spikes over time  →  (T, batch, neurons)
        spk_hidden = torch.stack(spk_hidden_rec)
        spk_out    = torch.stack(spk_out_rec)

        return spk_out, mem2, spk_hidden


# ============================================================
# GPU Monitoring
# ============================================================

class GPUMonitor:
    """Monitor GPU/CPU metrics during training"""
    
    def __init__(self):
        self.gpu_type = self.detect_gpu()
        self.device = self.get_device()
        self.nvml = None
        self.handle = None
        
        self.history = []
        self.start_time = None
        
        print("\n" + "="*70)
        print("GPU CONFIGURATION")
        print("="*70)
        print(f"GPU Type: {self.gpu_type}")
        print(f"Device: {self.device}")
        print("="*70)
    
    def detect_gpu(self):
        """Detect available GPU (NVIDIA, AMD, or CPU)"""
        
        # Try PyTorch CUDA first (works even without NVML!)
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
    
    def start_monitoring(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.history = []
    
    def record_metrics(self, epoch, accuracy, loss):
        """Record metrics for this epoch"""
        current_time = time.time() - self.start_time
        
        metrics = {
            'epoch': epoch,
            'accuracy': accuracy,
            'loss': loss,
            'time_seconds': current_time,
            'timestamp': datetime.now().isoformat(),
        }
        
        # RAM usage
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            metrics['ram_mb'] = process.memory_info().rss / (1024 * 1024)
        else:
            metrics['ram_mb'] = 0
        
        # GPU metrics
        if self.gpu_type in ['nvidia', 'nvidia_cuda']:
            if torch.cuda.is_available():
                metrics['gpu_allocated_mb'] = torch.cuda.memory_allocated() / (1024 * 1024)
                metrics['gpu_reserved_mb'] = torch.cuda.memory_reserved() / (1024 * 1024)
            
            # NVML power (if available)
            if self.gpu_type == 'nvidia' and self.nvml and self.handle:
                try:
                    power_mw = self.nvml.nvmlDeviceGetPowerUsage(self.handle)
                    metrics['power_watts'] = power_mw / 1000.0
                except:
                    metrics['power_watts'] = 115.0  # TDP estimate
            else:
                metrics['power_watts'] = 115.0  # TDP estimate
        else:
            metrics['gpu_allocated_mb'] = 0
            metrics['gpu_reserved_mb'] = 0
            metrics['power_watts'] = 0
        
        # Energy calculation
        if epoch > 1:
            prev_time = self.history[-1]['time_seconds']
            duration = current_time - prev_time
            metrics['energy_wh'] = metrics['power_watts'] * (duration / 3600.0)
        else:
            metrics['energy_wh'] = 0
        
        metrics['temperature_c'] = 0  # Will be filled by HWiNFO64 if available
        
        self.history.append(metrics)
        return metrics
    
    def get_summary(self):
        """Get summary statistics"""
        if not self.history:
            return {}
        
        total_time = self.history[-1]['time_seconds']
        final_accuracy = self.history[-1]['accuracy']
        max_ram = max(h['ram_mb'] for h in self.history)
        avg_power = sum(h['power_watts'] for h in self.history) / len(self.history)
        total_energy = sum(h['energy_wh'] for h in self.history)
        
        max_gpu_allocated = 0
        if self.gpu_type in ['nvidia', 'nvidia_cuda']:
            max_gpu_allocated = max(h.get('gpu_allocated_mb', 0) for h in self.history)
        
        gpu_reserved = 0
        if self.history and 'gpu_reserved_mb' in self.history[0]:
            gpu_reserved = self.history[0]['gpu_reserved_mb']
        
        return {
            'final_accuracy': final_accuracy,
            'max_ram_mb': max_ram,
            'max_gpu_allocated_mb': max_gpu_allocated,
            'average_power_watts': avg_power,
            'total_energy_wh': total_energy,
            'total_time_seconds': total_time,
            'gpu_type': self.gpu_type,
        }
    
    def save_metrics(self, filepath):
        """Save metrics to JSON"""
        summary = self.get_summary()
        
        data = {
            'summary': summary,
            'history': self.history,
            'framework': 'snnTorch',
            'neuromorphic': True,
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Metrics saved to: {filepath}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.nvml:
            try:
                self.nvml.nvmlShutdown()
            except:
                pass


# ============================================================
# Inference Timing
# ============================================================

def measure_inference_time(model, input_size, num_steps, num_tests=100, device='cpu'):
    """Measure inference time"""
    model.eval()
    times = []
    
    with torch.no_grad():
        # Warmup
        x = torch.randn(1, input_size).to(device)
        for _ in range(10):
            model(x, num_steps=num_steps)
        
        # Measure
        for _ in range(num_tests):
            x = torch.randn(1, input_size).to(device)
            start = time.time()
            model(x, num_steps=num_steps)
            end = time.time()
            times.append((end - start) * 1000)  # Convert to ms
    
    return {
        'num_tests': num_tests,
        'average_ms': np.mean(times),
        'minimum_ms': np.min(times),
        'maximum_ms': np.max(times),
        'std_dev_ms': np.std(times),
        'p50_ms': np.percentile(times, 50),
        'p95_ms': np.percentile(times, 95),
        'p99_ms': np.percentile(times, 99),
    }


def add_inference_metrics(filepath, inference_metrics):
    """Add inference metrics to existing JSON"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    data['inference_timing'] = inference_metrics
    data['summary']['avg_inference_ms'] = inference_metrics['average_ms']
    data['summary']['p95_inference_ms'] = inference_metrics['p95_ms']
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


# ============================================================
# Train with Use Case Data
# ============================================================

def train_use_case_snn(num_samples=500, num_epochs=20, hidden_size=64):
    """Train SNN on real use case scenarios"""
    
    print("\n" + "="*70)
    print("NEUROMORPHIC SNN - USE CASE TRAINING")
    print("="*70)
    print("\nFeatures:")
    print("  ✓ Proactive suggestions (fills idle time)")
    print("  ✓ Default preferences (learns from feedback)")
    print("  ✓ Context-aware (time, energy, calendar)")
    print("  ✓ Realistic use cases from requirements")
    print()
    
    # Initialize GPU monitor
    monitor = GPUMonitor()
    
    # Generate training data
    print(f"Generating {num_samples} use case scenarios...")
    X_train, y_train, scenarios = generate_use_case_training_data(num_samples)
    
    # Convert to tensors
    X_train = torch.tensor(X_train, dtype=torch.float32).to(monitor.device)
    y_train = torch.tensor(y_train, dtype=torch.long).to(monitor.device)
    
    print(f"✓ Generated {len(X_train)} training samples")
    print(f"  Input features: {X_train.shape[1]}")
    print(f"  Activity types: {len(ACTIVITY_LABELS)}")
    
    # Show sample scenarios
    print("\n" + "-"*70)
    print("SAMPLE TRAINING SCENARIOS:")
    print("-"*70)
    for i in range(5):
        s = scenarios[i]
        day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][s['day']]
        print(f"\n{day_name} {s['hour']:02d}:{s['minute']:02d} | "
              f"Energy: {s['energy']}/100 | "
              f"Idle: {s['idle_minutes']}min")
        print(f"  → {s['suggestion']}: {s['reason']}")
    print("-"*70)
    
    # Create model
    input_size = X_train.shape[1]
    output_size = len(ACTIVITY_LABELS)
    
    print(f"\nCreating neuromorphic SNN...")
    print(f"  Input: {input_size} features")
    print(f"  Hidden: {hidden_size} LIF neurons")
    print(f"  Output: {output_size} activity types")
    
    model = NeuromorphicActivitySNN(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        beta=0.9
    ).to(monitor.device)
    
    # Initialize weights
    with torch.no_grad():
        nn.init.xavier_uniform_(model.fc1.weight)
        nn.init.xavier_uniform_(model.fc2.weight)
    
    # Optimizer and loss
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    loss_fn = SF.ce_rate_loss()
    
    # Training
    monitor.start_monitoring()
    
    print(f"\nTraining for {num_epochs} epochs...")
    print("="*70)
    
    best_accuracy = 0
    epoch_output_rates  = []   # for heatmap across epochs
    epoch_hidden_rates  = []

    for epoch in range(num_epochs):
        model.train()
        optimizer.zero_grad()

        # Forward pass — now returns hidden spikes too
        spk_out, mem_out, spk_hidden = model(X_train, num_steps=30)

        # Loss
        loss = loss_fn(spk_out, y_train)

        # Backward
        loss.backward()
        optimizer.step()

        # Calculate accuracy
        with torch.no_grad():
            spike_counts = spk_out.sum(0)
            _, predicted = spike_counts.max(1)
            correct = (predicted == y_train).sum().item()
            accuracy = (correct / len(y_train)) * 100

            if accuracy > best_accuracy:
                best_accuracy = accuracy

        # Record metrics
        metrics = monitor.record_metrics(epoch + 1, accuracy, loss.item())

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:2d}/{num_epochs}: "
                  f"Loss={loss.item():.4f}, "
                  f"Acc={accuracy:5.1f}%, "
                  f"Best={best_accuracy:5.1f}%, "
                  f"Time={metrics['time_seconds']:.1f}s")

        # ── Spike visualisation ──────────────────────────────────────────────
        if VIZ_AVAILABLE:
            with torch.no_grad():
                # Use first sample for per-epoch plots
                spk_out_np    = spk_out.detach().cpu().numpy()     # (T, N, 20)
                spk_hidden_np = spk_hidden.detach().cpu().numpy()  # (T, N, 64)

                # Accumulate per-neuron firing rates for heatmaps
                epoch_output_rates.append(spk_out_np[:, 0, :].sum(0) / spk_out_np.shape[0])
                epoch_hidden_rates.append(spk_hidden_np[:, 0, :].sum(0) / spk_hidden_np.shape[0])

                do_plot = (PLOT_EPOCHS is None) or ((epoch + 1) in PLOT_EPOCHS)
                if do_plot:
                    print(f"\n  📊 Saving spike visualisations for epoch {epoch+1}...")
                    # Output-layer dashboard (raster + rate + heatmap so far)
                    _viz.plot_all(
                        spk_out_np,
                        layer_name="Output Layer",
                        epoch=epoch + 1,
                        neuron_labels=VIZ_LABELS,
                        epoch_rates=epoch_output_rates,
                    )
                    # Hidden-layer raster
                    _viz.plot_raster(
                        spk_hidden_np,
                        layer_name="Hidden Layer",
                        epoch=epoch + 1,
                    )
                    # Hidden-layer firing rate
                    _viz.plot_firing_rate(
                        spk_hidden_np,
                        layer_name="Hidden Layer",
                        epoch=epoch + 1,
                    )
    
    print("="*70)
    
    # Summary
    summary = monitor.get_summary()
    print(f"\nTraining Summary:")
    print(f"  Total time: {summary['total_time_seconds']:.1f} seconds")
    print(f"  Best accuracy: {best_accuracy:.1f}%")
    print(f"  Final accuracy: {summary['final_accuracy']:.1f}%")
    print(f"  Average power: {summary['average_power_watts']:.1f} W")
    print(f"  Total energy: {summary['total_energy_wh']:.4f} Wh")
    
    return model, monitor, best_accuracy


# ============================================================
# Test Proactive Suggestions
# ============================================================

def test_proactive_suggestions(model, device):
    """Test model on realistic scenarios"""
    
    print("\n" + "="*70)
    print("TESTING PROACTIVE SUGGESTIONS")
    print("="*70)
    
    model.eval()
    
    test_scenarios = [
        {
            'name': 'Monday 7 AM - 30min free before work',
            'features': [7/24, 0, 0/7, 0.8, 0.6, 30/180, 0, 0.5, 0.2, 0],
            'expected': 'workout or morning_activity',
        },
        {
            'name': 'Tuesday 12 PM - 1 hour lunch break',
            'features': [12/24, 0, 1/7, 0.6, 0.5, 60/180, 0, 0.5, 0.2, 0],
            'expected': 'lunch_break or light_activity',
        },
        {
            'name': 'Wednesday 3 PM - 15min idle, low energy',
            'features': [15/24, 0, 2/7, 0.3, 0.4, 15/180, 0, 0.5, 0.2, 0],
            'expected': 'quick_rest or stretch_break',
        },
        {
            'name': 'Friday 6 PM - 2 hours free evening',
            'features': [18/24, 0, 4/7, 0.5, 0.4, 120/180, 0, 0.5, 0.2, 0],
            'expected': 'relax or hobby_time',
        },
        {
            'name': 'Saturday 9 AM - 3 hours free weekend',
            'features': [9/24, 0, 5/7, 0.8, 0.7, 180/180, 0, 0.5, 0.2, 1],
            'expected': 'hobby_time or productive_project',
        },
        {
            'name': 'Monday 9 AM - meeting in 30min',
            'features': [9/24, 0, 0/7, 0.7, 0.8, 0/180, 1, 0.5, 0.2, 0],
            'expected': 'prepare_for_meeting',
        },
    ]
    
    with torch.no_grad():
        for scenario in test_scenarios:
            x = torch.tensor([scenario['features']], dtype=torch.float32).to(device)
            
            # Get prediction (model now returns 3 values)
            spk_out, mem_out, _ = model(x, num_steps=30)
            spike_counts = spk_out.sum(0)
            _, predicted = spike_counts.max(1)
            predicted_idx = predicted.item()
            predicted_activity = ACTIVITY_LABELS[predicted_idx]
            
            # Get confidence (spike count)
            confidence = spike_counts[0, predicted_idx].item()
            
            print(f"\n{scenario['name']}")
            print(f"  Expected: {scenario['expected']}")
            print(f"  Suggested: {predicted_activity}")
            print(f"  Confidence: {confidence:.1f} spikes")
    
    print("\n" + "="*70)


# ============================================================
# Save Model with Defaults
# ============================================================

def save_use_case_model(model, best_accuracy, filepath='minios_usecase_model.pth'):
    """Save model with use case metadata"""
    
    # Create default user profile
    default_profile = UserProfile()
    
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_size': model.input_size,
        'hidden_size': model.hidden_size,
        'output_size': model.output_size,
        'activity_labels': ACTIVITY_LABELS,
        'use_cases': USE_CASES,
        'default_preferences': default_profile.preferences,
        'best_accuracy': best_accuracy,
        'proactive': True,
        'fills_idle_time': True,
    }, filepath)
    
    print(f"\n✓ Model saved to: {filepath}")
    print(f"  Includes default preferences")
    print(f"  Includes use case metadata")
    print(f"  Best accuracy: {best_accuracy:.1f}%")


# ============================================================
# Main Training Pipeline
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("USE CASE SNN TRAINING")
    print("Proactive + Learning + Context-Aware")
    print("="*70)
    
    # Train model
    model, monitor, best_accuracy = train_use_case_snn(
        num_samples=500,
        num_epochs=20,
        hidden_size=64
    )
    
    # Save metrics
    monitor.save_metrics('usecase_training_metrics.json')
    
    # Add use case metadata
    with open('usecase_training_metrics.json', 'r') as f:
        data = json.load(f)
    
    data['use_cases'] = {
        'proactive': True,
        'fills_idle_time': True,
        'context_aware': True,
        'learns_preferences': True,
        'num_activities': len(ACTIVITY_LABELS),
        'activities': ACTIVITY_LABELS,
    }
    
    with open('usecase_training_metrics.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Test proactive suggestions
    test_proactive_suggestions(model, monitor.device)
    
    # Measure inference time
    inference_metrics = measure_inference_time(
        model,
        input_size=10,
        num_steps=30,
        num_tests=100,
        device=monitor.device
    )
    
    add_inference_metrics('usecase_training_metrics.json', inference_metrics)
    
    # Save model
    save_use_case_model(model, best_accuracy)
    
    # Cleanup
    monitor.cleanup()
    
    print("\n" + "="*70)
    print("✓ USE CASE TRAINING COMPLETE!")
    print("="*70)
    print(f"\nFiles created:")
    print(f"  - usecase_training_metrics.json")
    print(f"  - minios_usecase_model.pth")
    print(f"\nModel features:")
    print(f"  ✓ Proactive suggestions")
    print(f"  ✓ Fills idle time automatically")
    print(f"  ✓ Default preferences included")
    print(f"  ✓ Context-aware (time, energy, calendar)")
    print(f"  ✓ Ready for feedback learning")
    print(f"\nNext: python export_usecase_to_minios.py")
    print()
