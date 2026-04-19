#!/usr/bin/env python3
"""
Train Neuromorphic SNN on Real Use Cases
With default preferences and proactive suggestions

Usage:
    python train_usecase_snn.py --train          # Train and save model
    python train_usecase_snn.py --benchmark-gpu  # Measure GPU inference energy
    python train_usecase_snn.py --loihi          # Estimate Loihi 2 energy
"""

import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import snntorch as snn
from snntorch import surrogate
import numpy as np
import json
import time
from datetime import datetime

from use_case_data import (
    generate_use_case_training_data,
    ACTIVITY_LABELS,
    UserProfile,
    USE_CASES
)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available - RAM/CPU monitoring disabled")

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

MODEL_PATH   = 'minios_usecase_model.pth'
METRICS_PATH = 'usecase_training_metrics.json'


# ============================================================
# SNN Model
# ============================================================

class NeuromorphicActivitySNN(nn.Module):
    def __init__(self, input_size=10, hidden_size=64, output_size=20, beta=0.9):
        super().__init__()

        self.input_size  = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        spike_grad = surrogate.fast_sigmoid(slope=25)

        self.fc1  = nn.Linear(input_size, hidden_size)
        self.lif1 = snn.Leaky(beta=beta, spike_grad=spike_grad)

        self.fc2  = nn.Linear(hidden_size, output_size)
        self.lif2 = snn.Leaky(beta=beta, spike_grad=spike_grad)

    def forward(self, x, num_steps=20):
        mem1 = self.lif1.init_leaky()
        mem2 = self.lif2.init_leaky()

        spk_out_rec = []
        for _ in range(num_steps):
            cur1 = self.fc1(x)
            spk1, mem1 = self.lif1(cur1, mem1)
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)
            spk_out_rec.append(spk2)

        return torch.stack(spk_out_rec), mem2


# ============================================================
# GPU Monitor (used during --train and --benchmark-gpu)
# ============================================================

class GPUMonitor:
    def __init__(self):
        self.gpu_type   = self._detect_gpu()
        self.device     = self._get_device()
        self.nvml       = None
        self.handle     = None
        self.history    = []
        self.start_time = None

        print("\n" + "="*70)
        print("GPU CONFIGURATION")
        print("="*70)
        print(f"  GPU Type: {self.gpu_type}")
        print(f"  Device:   {self.device}")
        print("="*70)

    def _detect_gpu(self):
        if torch.cuda.is_available():
            print(f"✓ CUDA GPU: {torch.cuda.get_device_name(0)}")
            if NVML_AVAILABLE:
                try:
                    pynvml.nvmlInit()
                    self.nvml   = pynvml
                    self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    print("✓ NVML monitoring enabled")
                    return 'nvidia'
                except Exception as e:
                    print(f"⚠️  NVML disabled ({e})")
                    return 'nvidia_cuda'
            return 'nvidia_cuda'

        try:
            import torch_directml
            if torch_directml.is_available():
                print("✓ AMD GPU via DirectML")
                return 'amd_directml'
        except ImportError:
            pass

        print("⚠️  No GPU found — falling back to CPU")
        return 'cpu'

    def _get_device(self):
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
        self.start_time = time.time()
        self.history    = []

    def record_metrics(self, epoch, accuracy, loss):
        current_time = time.time() - self.start_time
        metrics = {
            'epoch':            epoch,
            'accuracy':         accuracy,
            'loss':             loss,
            'time_seconds':     current_time,
            'timestamp':        datetime.now().isoformat(),
            'ram_mb':           0,
            'gpu_allocated_mb': 0,
            'gpu_reserved_mb':  0,
            'power_watts':      0,
            'energy_wh':        0,
            'temperature_c':    0,
        }

        if PSUTIL_AVAILABLE:
            metrics['ram_mb'] = psutil.Process().memory_info().rss / (1024 * 1024)

        if self.gpu_type in ['nvidia', 'nvidia_cuda'] and torch.cuda.is_available():
            metrics['gpu_allocated_mb'] = torch.cuda.memory_allocated() / (1024 * 1024)
            metrics['gpu_reserved_mb']  = torch.cuda.memory_reserved()  / (1024 * 1024)

        if self.gpu_type == 'nvidia' and self.nvml and self.handle:
            try:
                metrics['power_watts'] = self.nvml.nvmlDeviceGetPowerUsage(self.handle) / 1000.0
            except:
                metrics['power_watts'] = 115.0
        elif self.gpu_type == 'nvidia_cuda':
            metrics['power_watts'] = 115.0

        if epoch > 1:
            duration = current_time - self.history[-1]['time_seconds']
            metrics['energy_wh'] = metrics['power_watts'] * (duration / 3600.0)

        self.history.append(metrics)
        return metrics

    def get_summary(self):
        if not self.history:
            return {}
        return {
            'final_accuracy':       self.history[-1]['accuracy'],
            'max_ram_mb':           max(h['ram_mb'] for h in self.history),
            'max_gpu_allocated_mb': max(h.get('gpu_allocated_mb', 0) for h in self.history),
            'average_power_watts':  sum(h['power_watts'] for h in self.history) / len(self.history),
            'total_energy_wh':      sum(h['energy_wh']   for h in self.history),
            'total_time_seconds':   self.history[-1]['time_seconds'],
            'gpu_type':             self.gpu_type,
        }

    def cleanup(self):
        if self.nvml:
            try:
                self.nvml.nvmlShutdown()
            except:
                pass


# ============================================================
# Shared helpers
# ============================================================

def load_model_from_disk():
    """Load saved model. Exits with a clear message if not found."""
    try:
        checkpoint = torch.load(MODEL_PATH, map_location='cpu')
    except FileNotFoundError:
        print(f"\n❌  Model file '{MODEL_PATH}' not found.")
        print(f"    Run  python train_usecase_snn.py --train  first.")
        raise SystemExit(1)

    model = NeuromorphicActivitySNN(
        input_size=checkpoint['input_size'],
        hidden_size=checkpoint['hidden_size'],
        output_size=checkpoint['output_size'],
        beta=0.9,
    )
    model.load_state_dict(checkpoint['model_state_dict'])

    print(f"✓ Loaded model from {MODEL_PATH}")
    print(f"  Architecture:  {checkpoint['input_size']} → "
          f"{checkpoint['hidden_size']} → {checkpoint['output_size']}")
    print(f"  Best accuracy: {checkpoint.get('best_accuracy', 'N/A')}")

    return model, checkpoint


def update_metrics_file(key, data):
    """Read metrics JSON, update one top-level key, write back."""
    try:
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
    except FileNotFoundError:
        metrics = {}

    metrics[key] = data

    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"✓ Saved '{key}' to {METRICS_PATH}")


# ============================================================
# --train
# ============================================================

def run_train(num_samples=500, num_epochs=20, hidden_size=64,
              batch_size=32, lr=0.01):

    print("\n" + "="*70)
    print("NEUROMORPHIC SNN — USE CASE TRAINING")
    print("="*70)

    monitor = GPUMonitor()

    print(f"\nGenerating {num_samples} use case scenarios...")
    X_train, y_train, scenarios = generate_use_case_training_data(num_samples)

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.long)

    print(f"✓ {len(X_train)} samples  |  "
          f"{X_train.shape[1]} features  |  "
          f"{len(ACTIVITY_LABELS)} activity classes")

    class_counts  = torch.bincount(y_train, minlength=len(ACTIVITY_LABELS)).float()
    class_weights = 1.0 / (class_counts + 1e-6)
    class_weights = (class_weights / class_weights.sum() * len(ACTIVITY_LABELS)).to(monitor.device)

    dataset = TensorDataset(X_train, y_train)
    loader  = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=False)

    print("\nSample scenarios:")
    for i in range(3):
        s   = scenarios[i]
        day = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][s['day']]
        print(f"  {day} {s['hour']:02d}:{s['minute']:02d} | "
              f"energy={s['energy']} | idle={s['idle_minutes']}min "
              f"→ {s['suggestion']}")

    input_size  = X_train.shape[1]
    output_size = len(ACTIVITY_LABELS)

    model = NeuromorphicActivitySNN(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        beta=0.9,
    ).to(monitor.device)

    with torch.no_grad():
        nn.init.xavier_uniform_(model.fc1.weight)
        nn.init.xavier_uniform_(model.fc2.weight)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=num_epochs, eta_min=1e-4
    )

    monitor.start_monitoring()
    print(f"\nTraining {num_epochs} epochs...")
    print("="*70)

    best_accuracy    = 0
    best_model_state = None

    for epoch in range(num_epochs):
        model.train()
        epoch_loss = epoch_correct = epoch_total = 0

        for X_batch, y_batch in loader:
            X_batch = X_batch.to(monitor.device)
            y_batch = y_batch.to(monitor.device)

            optimizer.zero_grad()
            spk_out, _ = model(X_batch, num_steps=30)
            spike_counts = spk_out.sum(0)
            loss = F.cross_entropy(spike_counts, y_batch, weight=class_weights)
            loss.backward()
            optimizer.step()

            with torch.no_grad():
                _, predicted  = spike_counts.max(1)
                epoch_correct += (predicted == y_batch).sum().item()
                epoch_total   += y_batch.size(0)
                epoch_loss    += loss.item() * y_batch.size(0)

        scheduler.step()

        accuracy = (epoch_correct / epoch_total) * 100
        avg_loss = epoch_loss / epoch_total

        if accuracy > best_accuracy:
            best_accuracy    = accuracy
            best_model_state = {k: v.clone() for k, v in model.state_dict().items()}

        metrics = monitor.record_metrics(epoch + 1, accuracy, avg_loss)

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{num_epochs}  "
                  f"loss={avg_loss:.4f}  acc={accuracy:5.1f}%  "
                  f"best={best_accuracy:5.1f}%  "
                  f"t={metrics['time_seconds']:.1f}s")

    if best_model_state:
        model.load_state_dict(best_model_state)
        print(f"\n✓ Best weights restored  (accuracy: {best_accuracy:.1f}%)")

    # Save model
    default_profile = UserProfile()
    torch.save({
        'model_state_dict':    model.state_dict(),
        'input_size':          model.input_size,
        'hidden_size':         model.hidden_size,
        'output_size':         model.output_size,
        'activity_labels':     ACTIVITY_LABELS,
        'use_cases':           USE_CASES,
        'default_preferences': default_profile.preferences,
        'best_accuracy':       best_accuracy,
        'proactive':           True,
        'fills_idle_time':     True,
    }, MODEL_PATH)
    print(f"✓ Model saved to {MODEL_PATH}")

    # Save training metrics
    summary = monitor.get_summary()
    update_metrics_file('summary', summary)
    update_metrics_file('history', monitor.history)

    monitor.cleanup()

    print("\n" + "="*70)
    print("✓ TRAINING COMPLETE")
    print("="*70)
    print(f"  Best accuracy: {best_accuracy:.1f}%")
    print(f"\nNext:")
    print(f"  python train_usecase_snn.py --benchmark-gpu")
    print(f"  python train_usecase_snn.py --loihi")


# ============================================================
# --benchmark-gpu
# ============================================================

def run_benchmark_gpu(num_tests=100, num_steps=30):

    print("\n" + "="*70)
    print("GPU INFERENCE ENERGY BENCHMARK")
    print("="*70)

    model, _ = load_model_from_disk()
    monitor  = GPUMonitor()
    model    = model.to(monitor.device)
    model.eval()

    # Warmup
    print("\nWarming up...")
    with torch.no_grad():
        x = torch.randn(1, model.input_size).to(monitor.device)
        for _ in range(10):
            model(x, num_steps=num_steps)

    # Benchmark
    print(f"Running {num_tests} inference passes on {monitor.gpu_type}...")
    times = []
    with torch.no_grad():
        for _ in range(num_tests):
            x     = torch.randn(1, model.input_size).to(monitor.device)
            start = time.time()
            model(x, num_steps=num_steps)
            times.append((time.time() - start) * 1000)

    avg_ms = float(np.mean(times))
    p95_ms = float(np.percentile(times, 95))

    # Power — NVML if available, else AMD measured baseline
    summary      = monitor.get_summary()
    gpu_power_w  = summary.get('average_power_watts', 0.0)
    power_source = 'nvml_measured'
    if gpu_power_w < 1.0:
        gpu_power_w  = 24.5   # your AMD DirectML measured baseline
        power_source = 'amd_measured_baseline'

    energy_per_inference_uJ = gpu_power_w * (avg_ms / 1000.0) * 1e6
    daily_energy_wh         = energy_per_inference_uJ * 86400 / 3.6e9

    result = {
        'device':                   str(monitor.device),
        'gpu_type':                 monitor.gpu_type,
        'num_tests':                num_tests,
        'num_steps':                num_steps,
        'average_ms':               avg_ms,
        'p95_ms':                   p95_ms,
        'power_w':                  gpu_power_w,
        'power_source':             power_source,
        'energy_per_inference_uJ':  energy_per_inference_uJ,
        'daily_energy_wh':          daily_energy_wh,
        'inferences_per_day':       86400,
        'timestamp':                datetime.now().isoformat(),
    }

    print("\n" + "="*70)
    print("RESULTS — GPU")
    print("="*70)
    print(f"  Device:              {monitor.gpu_type}")
    print(f"  Avg latency:         {avg_ms:.2f} ms")
    print(f"  p95 latency:         {p95_ms:.2f} ms")
    print(f"  Power draw:          {gpu_power_w:.1f} W  ({power_source})")
    print(f"  Energy/inference:    {energy_per_inference_uJ:.2f} µJ")
    print(f"  Daily energy (24/7): {daily_energy_wh:.4f} Wh")
    print("="*70)

    update_metrics_file('gpu_benchmark', result)
    monitor.cleanup()

    print(f"\nNext: python train_usecase_snn.py --loihi")


# ============================================================
# --loihi
# ============================================================

def run_loihi_estimate(num_steps=30, avg_spike_rate=0.1):

    print("\n" + "="*70)
    print("LOIHI 2 ENERGY ESTIMATE")
    print("="*70)

    model, _ = load_model_from_disk()

    input_size  = model.input_size
    hidden_size = model.hidden_size
    output_size = model.output_size

    synapses_l1 = input_size  * hidden_size
    synapses_l2 = hidden_size * output_size

    # SOPs fire only when a pre-synaptic neuron spikes
    sops_l1    = avg_spike_rate * synapses_l1 * num_steps
    sops_l2    = avg_spike_rate * synapses_l2 * num_steps
    total_sops = sops_l1 + sops_l2

    ENERGY_PER_SOP_PJ = 3.0    # Intel Loihi 2 published figure (pJ per SOP)
    # Core static power for a small network on a single neurocore.
    # Full chip idle is ~30 mW but that is spread across 128 neurocores.
    # This model fits on ~1 neurocore, so static ≈ 30 mW / 128 ≈ 0.23 mW.
    # We use 0.001 W (1 mW) as a conservative single-core estimate.
    CORE_STATIC_W = 0.001  # 1 mW — single neurocore static power

    dynamic_energy_pJ = total_sops * ENERGY_PER_SOP_PJ
    dynamic_energy_uJ = dynamic_energy_pJ / 1e6  # pJ → µJ

    # Loihi runs ~1 ms per timestep
    # Static energy (µJ) = W × s × 1e6
    estimated_latency_ms = float(num_steps) * 1.0
    estimated_latency_s  = estimated_latency_ms / 1000.0
    static_energy_uJ     = CORE_STATIC_W * estimated_latency_s * 1e6

    total_energy_uJ = dynamic_energy_uJ + static_energy_uJ
    daily_energy_wh = total_energy_uJ * 86400 / 3.6e9

    result = {
        'device':                   'loihi2_estimated',
        'energy_per_sop_pJ':        ENERGY_PER_SOP_PJ,
        'core_static_power_w':      CORE_STATIC_W,
        'num_steps':                num_steps,
        'avg_spike_rate':           avg_spike_rate,
        'synapses_layer1':          synapses_l1,
        'synapses_layer2':          synapses_l2,
        'total_sops_per_inference': int(total_sops),
        'dynamic_energy_uJ':        dynamic_energy_uJ,
        'static_energy_uJ':         static_energy_uJ,
        'total_energy_uJ':          total_energy_uJ,
        'estimated_latency_ms':     estimated_latency_ms,
        'daily_energy_wh':          daily_energy_wh,
        'inferences_per_day':       86400,
        'timestamp':                datetime.now().isoformat(),
        'note': (
            f"Based on Intel Loihi 2 published 3 pJ/SOP. "
            f"Assumes {avg_spike_rate*100:.0f}% spike rate (sparse SNN). "
            f"Dynamic energy scales down further with sparser activity."
        ),
    }

    print("\n" + "="*70)
    print("RESULTS — LOIHI 2 (estimated)")
    print("="*70)
    print(f"  Model:               {input_size} → {hidden_size} → {output_size}")
    print(f"  Timesteps:           {num_steps}")
    print(f"  Avg spike rate:      {avg_spike_rate*100:.0f}%")
    print(f"  Total SOPs/inf:      {int(total_sops):,}")
    print(f"  Dynamic energy:      {dynamic_energy_uJ:.6f} µJ")
    print(f"  Static energy:       {static_energy_uJ:.6f} µJ")
    print(f"  Total energy/inf:    {total_energy_uJ:.6f} µJ")
    print(f"  Est. latency:        {estimated_latency_ms:.1f} ms")
    print(f"  Daily energy (24/7): {daily_energy_wh:.8f} Wh")
    print("="*70)
    print(f"  Note: {result['note']}")
    print("="*70)

    # If GPU benchmark already exists, print savings immediately
    try:
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
        gpu = metrics.get('gpu_benchmark')
        if gpu:
            gpu_uJ    = gpu['energy_per_inference_uJ']
            savings_x = gpu_uJ / max(total_energy_uJ, 1e-9)
            gpu_daily = gpu['daily_energy_wh']
            print(f"\n  vs GPU ({gpu['gpu_type']}):")
            print(f"    Energy savings:      {savings_x:.0f}× less per inference")
            print(f"    Daily Wh saved:      {gpu_daily - daily_energy_wh:.4f} Wh")
            print("="*70)
    except (FileNotFoundError, KeyError):
        print(f"\n  Tip: run --benchmark-gpu first to see GPU vs Loihi savings.")

    update_metrics_file('loihi_estimate', result)


# ============================================================
# Argparse entry point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="MiniOS Neuromorphic SNN — train, benchmark GPU, or estimate Loihi energy"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--train',
        action='store_true',
        help='Train the SNN and save model to minios_usecase_model.pth',
    )
    group.add_argument(
        '--benchmark-gpu',
        action='store_true',
        dest='benchmark_gpu',
        help='Measure real GPU inference energy (requires saved model)',
    )
    group.add_argument(
        '--loihi',
        action='store_true',
        help='Estimate Loihi 2 inference energy from model architecture (requires saved model)',
    )

    args = parser.parse_args()

    if args.train:
        run_train()
    elif args.benchmark_gpu:
        run_benchmark_gpu()
    elif args.loihi:
        run_loihi_estimate()


if __name__ == "__main__":
    main()