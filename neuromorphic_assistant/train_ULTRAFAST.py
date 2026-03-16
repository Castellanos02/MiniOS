#!/usr/bin/env python3
"""
ULTRA-FAST SNN Training for Quick Testing
5 epochs, 20 samples - completes in ~30 seconds!
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
# Quick GPU Monitor (Simplified)
# ============================================================

class QuickGPUMonitor:
    """Simplified GPU monitor for fast testing"""
    
    def __init__(self):
        self.gpu_type = self.detect_gpu()
        self.metrics_history = []
        self.start_time = None
        
    def detect_gpu(self):
        """Detect GPU quickly"""
        try:
            import torch_directml
            if torch_directml.is_available():
                print(f"✓ AMD GPU via DirectML")
                return 'amd_directml'
        except:
            pass
        
        try:
            import pynvml
            pynvml.nvmlInit()
            if pynvml.nvmlDeviceGetCount() > 0:
                self.nvml = pynvml
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                print(f"✓ NVIDIA GPU")
                return 'nvidia'
        except:
            pass
        
        print("⚠ CPU only")
        return 'cpu'
    
    def get_metrics(self):
        """Get current metrics"""
        metrics = {
            'ram_mb': 0,
            'gpu_allocated_mb': 0,
            'gpu_reserved_mb': 0,
            'power_watts': 0,
            'temperature_c': 0,
        }
        
        # RAM
        try:
            import psutil
            metrics['ram_mb'] = psutil.Process().memory_info().rss / (1024 * 1024)
        except:
            pass
        
        # GPU metrics
        if self.gpu_type == 'nvidia':
            try:
                mem = self.nvml.nvmlDeviceGetMemoryInfo(self.handle)
                metrics['gpu_allocated_mb'] = mem.used / (1024 * 1024)
                metrics['gpu_reserved_mb'] = mem.total / (1024 * 1024)
                metrics['power_watts'] = self.nvml.nvmlDeviceGetPowerUsage(self.handle) / 1000.0
                metrics['temperature_c'] = self.nvml.nvmlDeviceGetTemperature(self.handle, 0)
            except:
                pass
        elif self.gpu_type == 'amd_directml':
            # Estimates for AMD
            metrics['gpu_allocated_mb'] = metrics['ram_mb']
            metrics['gpu_reserved_mb'] = 4096
            metrics['power_watts'] = 130.0
            metrics['temperature_c'] = 65
        
        return metrics
    
    def start_monitoring(self):
        self.start_time = time.time()
        self.metrics_history = []
    
    def record_metrics(self, epoch, accuracy, loss):
        elapsed = time.time() - self.start_time
        m = self.get_metrics()
        
        metrics = {
            'epoch': epoch,
            'accuracy': accuracy,
            'loss': loss,
            'time_seconds': elapsed,
            'ram_mb': m['ram_mb'],
            'gpu_allocated_mb': m['gpu_allocated_mb'],
            'gpu_reserved_mb': m['gpu_reserved_mb'],
            'power_watts': m['power_watts'],
            'energy_wh': (m['power_watts'] * elapsed) / 3600.0,
            'temperature_c': m['temperature_c'],
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def get_summary(self):
        if not self.metrics_history:
            return {}
        
        last = self.metrics_history[-1]
        
        return {
            'total_time_seconds': last['time_seconds'],
            'total_energy_wh': last['energy_wh'],
            'final_accuracy': last['accuracy'],
            'average_power_watts': np.mean([m['power_watts'] for m in self.metrics_history]),
            'max_ram_mb': max([m['ram_mb'] for m in self.metrics_history]),
            'max_gpu_allocated_mb': max([m['gpu_allocated_mb'] for m in self.metrics_history]),
            'gpu_type': self.gpu_type,
        }
    
    def save_metrics(self, filepath='training_metrics.json'):
        with open(filepath, 'w') as f:
            json.dump({
                'summary': self.get_summary(),
                'history': self.metrics_history,
                'gpu_type': self.gpu_type,
            }, f, indent=2)
        print(f"✓ Metrics saved to: {filepath}")


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


def generate_training_data(num_samples=20):
    """Generate minimal training data"""
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
        
        # Simple activity labels
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


def quick_train(num_epochs=5, num_samples=20, hidden_size=16, timesteps=10):
    """Ultra-fast training for testing"""
    
    print("=" * 70)
    print("⚡ ULTRA-FAST SNN TRAINING - FOR TESTING ONLY")
    print("=" * 70)
    print(f"\n⚡ OPTIMIZED FOR SPEED:")
    print(f"  - Epochs: {num_epochs} (vs 15 normal)")
    print(f"  - Samples: {num_samples} (vs 100 normal)")
    print(f"  - Hidden neurons: {hidden_size} (vs 32 normal)")
    print(f"  - Timesteps: {timesteps} (vs 30 normal)")
    print(f"\n⏱️ Expected time: ~30 seconds")
    print(f"⚠️  Lower accuracy expected - for testing only!\n")
    
    # Initialize monitor
    monitor = QuickGPUMonitor()
    
    # Create model
    params = Model_Params(
        input_size=None,
        hidden_layers=[hidden_size],
        output_size=len(ACTIVITY_CLASSES),
        steps=timesteps,
    )
    
    assistant = PersonalAssistant(params, class_names=ACTIVITY_CLASSES)
    
    # Generate data
    print(f"Generating {num_samples} training samples...")
    training_data = generate_training_data(num_samples)
    
    # Start monitoring
    monitor.start_monitoring()
    
    print(f"\nTraining for {num_epochs} epochs...")
    print("-" * 70)
    
    for epoch in range(num_epochs):
        epoch_start = time.time()
        total_loss = 0.0
        correct = 0
        
        for context, true_idx in training_data:
            pred_idx, pred_name, rates = assistant.suggest(context)
            feedback = "accept" if pred_idx == true_idx else "reject"
            if feedback == "accept":
                correct += 1
            loss = assistant.update_from_feedback(context, pred_idx, feedback, lr=0.02)
            total_loss += loss
        
        accuracy = (correct / len(training_data)) * 100
        avg_loss = total_loss / len(training_data)
        
        # Record metrics
        metrics = monitor.record_metrics(epoch + 1, accuracy, avg_loss)
        
        print(f"Epoch {epoch+1:2d}/{num_epochs}: "
              f"Loss={avg_loss:.4f}, "
              f"Acc={accuracy:5.1f}%, "
              f"Time={metrics['time_seconds']:.1f}s")
    
    print("-" * 70)
    
    # Summary
    summary = monitor.get_summary()
    print(f"\nTraining Summary:")
    print(f"  Total time: {summary['total_time_seconds']:.1f} seconds")
    print(f"  Final accuracy: {summary['final_accuracy']:.1f}%")
    print(f"  Total energy: {summary['total_energy_wh']:.4f} Wh")
    
    # Measure inference time
    print("\n" + "=" * 70)
    print("MEASURING INFERENCE TIME")
    print("=" * 70)
    
    inference_times = []
    num_tests = 50  # Fewer tests for speed
    
    print(f"\nRunning {num_tests} inference tests...")
    
    for i in range(num_tests):
        hour = np.random.randint(6, 24)
        minute = np.random.randint(0, 60)
        energy = np.random.randint(20, 100)
        engagement = np.random.randint(0, 100)
        
        context = create_minios_context(
            hour, minute, energy, engagement, 
            np.random.rand(), 0, 0
        )
        
        start_time = time.time()
        pred_idx, pred_name, rates = assistant.suggest(context)
        elapsed_ms = (time.time() - start_time) * 1000.0
        
        inference_times.append(elapsed_ms)
    
    avg_inference = np.mean(inference_times)
    p95_inference = np.percentile(inference_times, 95)
    
    print(f"✓ Inference time: {avg_inference:.2f} ms (avg), {p95_inference:.2f} ms (P95)")
    
    # Save metrics
    monitor.save_metrics('training_metrics.json')
    
    # Add inference metrics
    with open('training_metrics.json', 'r') as f:
        data = json.load(f)
    
    data['inference_timing'] = {
        'num_tests': num_tests,
        'average_ms': float(avg_inference),
        'p95_ms': float(p95_inference),
    }
    data['summary']['avg_inference_ms'] = float(avg_inference)
    
    with open('training_metrics.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Save model
    model = assistant.model
    np.savez(
        'minios_activity_model.npz',
        Weight_input_hidden=model.Weight_input_hidden,
        Weight_hidden_output=model.Weight_hidden_output,
        input_size=assistant.params.input_size,
        hidden_size=assistant.params.hidden_layers[0],
        output_size=assistant.params.output_size,
        steps=assistant.params.steps,
        class_names=assistant.class_names,
    )
    
    print(f"\n✓ Model saved to: minios_activity_model.npz")
    
    return assistant, monitor


if __name__ == "__main__":
    print("\n⚡ ULTRA-FAST SNN TRAINING")
    print("Perfect for quick testing and validation!\n")
    
    assistant, monitor = quick_train(
        num_epochs=5,
        num_samples=20,
        hidden_size=16,
        timesteps=10,
    )
    
    print("\n✓ Training complete!")
    print("  - Model: minios_activity_model.npz")
    print("  - Metrics: training_metrics.json")
    print("\n⚠️  Note: Lower accuracy expected (quick test mode)")
    print("    For production, use train_with_directml.py")
    print("\nNext step: python export_to_minios.py")
    print()
