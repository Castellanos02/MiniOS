#!/usr/bin/env python3
"""
Train Neuromorphic SNN on Real Use Cases
With default preferences and proactive suggestions

Usage:
    python train_usecase_snn.py --train          # Train and save model
    python train_usecase_snn.py --benchmark-gpu  # Measure GPU inference energy
    python train_usecase_snn.py --loihi          # Estimate Loihi 2 energy
    python train_usecase_snn.py --ops-estimate   # Measure real SOPs
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

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

DATASET_PATH = 'general_assistant_dataset_update.csv'

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available - RAM/CPU monitoring disabled")

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

MODEL_PATH = 'minios_usecase_model.pth'

def _detect_gpu_type() -> str:
    """Lightweight GPU detection - no monitor object needed."""
    if torch.cuda.is_available():
        return 'nvidia'
    try:
        import torch_directml
        if torch_directml.is_available():
            return 'amd_directml'
    except ImportError:
        pass
    return 'cpu'

def get_metrics_path(gpu_type: str) -> str:
    """Return a GPU-specific metrics filename so AMD and NVIDIA runs never overwrite each other."""
    mapping = {
        'nvidia':        'usecase_training_metrics_nvidia.json',
        'nvidia_cuda':   'usecase_training_metrics_nvidia.json',
        'amd_directml':  'usecase_training_metrics_amd.json',
        'cpu':           'usecase_training_metrics_cpu.json',
    }
    return mapping.get(gpu_type, f'usecase_training_metrics_{gpu_type}.json')


class NeuromorphicActivitySNN(nn.Module):
    def __init__(self, input_size, hidden_size=64, output_size=10, beta=0.9, dropout=0.25):
        super().__init__()

        self.input_size  = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        spike_grad = surrogate.fast_sigmoid(slope=25)

        self.fc1     = nn.Linear(input_size, hidden_size)
        self.lif1    = snn.Leaky(beta=beta, spike_grad=spike_grad)
        self.drop    = nn.Dropout(p=dropout)

        self.fc2  = nn.Linear(hidden_size, output_size)
        self.lif2 = snn.Leaky(beta=beta, spike_grad=spike_grad)

    def forward(self, x, num_steps=20):
        mem1 = self.lif1.init_leaky()
        mem2 = self.lif2.init_leaky()

        spk_out_rec = []
        for _ in range(num_steps):
            cur1 = self.fc1(x)
            spk1, mem1 = self.lif1(cur1, mem1)
            spk1 = self.drop(spk1)
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)
            spk_out_rec.append(spk2)

        return torch.stack(spk_out_rec), mem2


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
            print(f"CUDA GPU: {torch.cuda.get_device_name(0)}")
            if NVML_AVAILABLE:
                try:
                    pynvml.nvmlInit()
                    self.nvml   = pynvml
                    self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    print("NVML monitoring enabled")
                    return 'nvidia'
                except Exception as e:
                    print(f"NVML disabled ({e})")
                    return 'nvidia_cuda'
            return 'nvidia_cuda'

        try:
            import torch_directml
            if torch_directml.is_available():
                print("AMD GPU via DirectML")
                return 'amd_directml'
        except ImportError:
            pass

        print("No GPU found - falling back to CPU")
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

    def record_metrics(self, epoch, accuracy, loss, val_accuracy=None, val_loss=None):
        current_time = time.time() - self.start_time
        metrics = {
            'epoch':            epoch,
            'train_accuracy':   accuracy,
            'train_loss':       loss,
            'val_accuracy':     val_accuracy,
            'val_loss':         val_loss,
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
            'final_accuracy':       self.history[-1]['train_accuracy'],
            'final_val_accuracy':   self.history[-1].get('val_accuracy', 0),
            'final_val_loss':       self.history[-1].get('val_loss', 0),
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


def load_model_from_disk():
    """Load saved model. Exits with a clear message if not found."""
    try:
        checkpoint = torch.load(MODEL_PATH, map_location='cpu')
    except FileNotFoundError:
        print(f"\nModel file '{MODEL_PATH}' not found.")
        print(f"Run  python train_usecase_snn.py --train  first.")
        raise SystemExit(1)

    model = NeuromorphicActivitySNN(
        input_size=checkpoint['input_size'],
        hidden_size=checkpoint['hidden_size'],
        output_size=checkpoint['output_size'],
        beta=0.9,
    )
    model.load_state_dict(checkpoint['model_state_dict'])

    print(f"Loaded model from {MODEL_PATH}")
    print(f"  Architecture:  {checkpoint['input_size']} → "
          f"{checkpoint['hidden_size']} → {checkpoint['output_size']}")
    print(f"  Best accuracy: {checkpoint.get('best_accuracy', 'N/A')}")

    return model, checkpoint


def update_metrics_file(key, data, metrics_path: str):
    """Read metrics JSON, update one top-level key, write back."""
    try:
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
    except FileNotFoundError:
        metrics = {}

    metrics[key] = data

    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f" Saved '{key}' to {metrics_path}")



def run_train(num_epochs=200, hidden_size=64, batch_size=32, lr=0.001):

    print("\n" + "="*70)
    print("NEUROMORPHIC SNN - DRIVING ASSISTANT TRAINING")
    print("="*70)

    monitor = GPUMonitor()

    print(f"\nLoading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    print(f"  Loaded {len(df)} rows  |  {df['suggestion_name'].nunique()} classes")

    # Encode categorical columns
    cat_cols = ['time_of_day', 'event_category', 'scheduled_event',
                'location', 'weather', 'last_media']
    for col in cat_cols:
        df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    # Features: everything except label columns
    drop_cols = ['suggestion_name', 'suggestion_label']
    feature_cols = [c for c in df.columns if c not in drop_cols]
    X_all = df[feature_cols].values.astype(np.float32)
    y_all = df['suggestion_label'].values.astype(np.int64)

    suggestion_labels = sorted(df['suggestion_name'].unique())
    num_classes       = len(suggestion_labels)

    # 70-20-10 split
    X_tr, X_te, y_tr, y_te = train_test_split(X_all, y_all, test_size=0.10, random_state=42, stratify=y_all)
    X_tr, X_va, y_tr, y_va = train_test_split(X_tr,  y_tr,  test_size=0.222, random_state=42, stratify=y_tr)
    print(f"  Split (70-20-10):  train={len(X_tr)}  val={len(X_va)}  test={len(X_te)}")

    # Normalise features - fit on train only to avoid data leakage
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X_tr)
    X_va = scaler.transform(X_va)
    X_te = scaler.transform(X_te)

    X_train = torch.tensor(X_tr, dtype=torch.float32)
    y_train = torch.tensor(y_tr, dtype=torch.long)
    X_val   = torch.tensor(X_va, dtype=torch.float32)
    y_val   = torch.tensor(y_va, dtype=torch.long)
    X_test  = torch.tensor(X_te, dtype=torch.float32)
    y_test  = torch.tensor(y_te, dtype=torch.long)

    print(f"  {len(X_train)} train samples  |  "
          f"{X_train.shape[1]} features  |  "
          f"{num_classes} suggestion classes")

    class_counts  = torch.bincount(y_train, minlength=num_classes).float()
    class_weights = 1.0 / (class_counts + 1e-6)
    class_weights = (class_weights / class_weights.sum() * num_classes).to(monitor.device)

    train_dataset = TensorDataset(X_train, y_train)
    loader        = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    val_dataset   = TensorDataset(X_val, y_val)
    val_loader    = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    input_size  = X_train.shape[1]
    output_size = num_classes

    model = NeuromorphicActivitySNN(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        beta=0.9,
    ).to(monitor.device)

    with torch.no_grad():
        nn.init.xavier_uniform_(model.fc1.weight)
        nn.init.xavier_uniform_(model.fc2.weight)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=num_epochs, eta_min=1e-4
    )

    monitor.start_monitoring()
    print(f"\nTraining {num_epochs} epochs...")
    print("="*70)

    best_accuracy      = 0
    best_model_state   = None
    early_stop_patience = 30
    epochs_no_improve  = 0

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

        model.eval()
        val_correct = val_total = 0
        val_loss_sum = 0.0
        with torch.no_grad():
            for Xv, yv in val_loader:
                Xv, yv = Xv.to(monitor.device), yv.to(monitor.device)
                spk_v, _ = model(Xv, num_steps=30)
                spike_counts_v = spk_v.sum(0)
                v_loss = F.cross_entropy(spike_counts_v, yv, weight=class_weights)
                _, pred_v = spike_counts_v.max(1)
                val_correct  += (pred_v == yv).sum().item()
                val_total    += yv.size(0)
                val_loss_sum += v_loss.item() * yv.size(0)
        val_accuracy = (val_correct / val_total) * 100
        val_avg_loss = val_loss_sum / val_total

        if val_accuracy > best_accuracy:
            best_accuracy    = val_accuracy
            best_model_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        metrics = monitor.record_metrics(epoch + 1, accuracy, avg_loss, val_accuracy, val_avg_loss)

        if True:
            print(f"Epoch {epoch+1:3d}/{num_epochs}  "
                  f"loss={avg_loss:.4f}  train_acc={accuracy:5.1f}%  "
                  f"val_acc={val_accuracy:5.1f}%  "
                  f"best_val={best_accuracy:5.1f}%  "
                  f"t={metrics['time_seconds']:.1f}s")

    if best_model_state:
        model.load_state_dict(best_model_state)
        print(f"\n  Best val weights restored  (val_acc: {best_accuracy:.1f}%)")

    model.eval()
    test_correct = test_total = 0
    test_loader  = DataLoader(TensorDataset(X_test, y_test), batch_size=batch_size)
    with torch.no_grad():
        for Xt, yt in test_loader:
            Xt, yt = Xt.to(monitor.device), yt.to(monitor.device)
            spk_t, _ = model(Xt, num_steps=30)
            _, pred_t = spk_t.sum(0).max(1)
            test_correct += (pred_t == yt).sum().item()
            test_total   += yt.size(0)
    test_accuracy = (test_correct / test_total) * 100
    print(f"  Test-set accuracy: {test_accuracy:.1f}%")

    # Inline 100-pass inference benchmark (matches train_usecase_dnn.py method)
    single_x = X_test[:1].to(monitor.device)
    latency_times = []
    with torch.no_grad():
        for _ in range(10):                         # warmup
            model(single_x, num_steps=30)
        for _ in range(100):
            t0 = time.time()
            model(single_x, num_steps=30)
            latency_times.append((time.time() - t0) * 1000)
    avg_inference_ms = float(np.mean(latency_times))
    p95_inference_ms = float(np.percentile(latency_times, 95))
    print(f"  Avg inference:     {avg_inference_ms:.3f} ms")
    print(f"  p95 inference:     {p95_inference_ms:.3f} ms")

    # Save model
    torch.save({
        'model_state_dict':    model.state_dict(),
        'input_size':          model.input_size,
        'hidden_size':         model.hidden_size,
        'output_size':         model.output_size,
        'suggestion_labels':   suggestion_labels,
        'dataset_path':        DATASET_PATH,
        'best_val_accuracy':   best_accuracy,
        'test_accuracy':       test_accuracy,
        'split_mode':          '70-20-10',
        'num_samples':         len(df),
    }, MODEL_PATH)
    print(f"  Model saved to {MODEL_PATH}")

    # Save training metrics to GPU-specific file
    metrics_path = get_metrics_path(monitor.gpu_type)
    summary = monitor.get_summary()
    summary['test_accuracy']     = test_accuracy
    summary['dataset_path']      = DATASET_PATH
    summary['model_type']        = 'snn'
    summary['avg_inference_ms']  = avg_inference_ms
    summary['p95_inference_ms']  = p95_inference_ms
    update_metrics_file('summary', summary, metrics_path)
    update_metrics_file('history', monitor.history, metrics_path)

    monitor.cleanup()

    print("\n" + "="*70)
    print("  TRAINING COMPLETE")
    print("="*70)
    print(f"  Best val accuracy : {best_accuracy:.1f}%")
    print(f"  Test accuracy     : {test_accuracy:.1f}%")
    print(f"  Avg inference     : {avg_inference_ms:.3f} ms")
    print(f"\nNext:")
    print(f"  python train_usecase_snn.py --benchmark-gpu")
    print(f"  python train_usecase_snn.py --loihi")


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

    # Power - NVML if available, else AMD measured baseline
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
    print("RESULTS - GPU")
    print("="*70)
    print(f"  Device:              {monitor.gpu_type}")
    print(f"  Avg latency:         {avg_ms:.2f} ms")
    print(f"  p95 latency:         {p95_ms:.2f} ms")
    print(f"  Power draw:          {gpu_power_w:.1f} W  ({power_source})")
    print(f"  Energy/inference:    {energy_per_inference_uJ:.2f} µJ")
    print(f"  Daily energy (24/7): {daily_energy_wh:.4f} Wh")
    print("="*70)

    update_metrics_file('gpu_benchmark', result, get_metrics_path(monitor.gpu_type))
    monitor.cleanup()

    print(f"\nNext: python train_usecase_snn.py --loihi")


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
    CORE_STATIC_W = 0.001  # 1 mW - single neurocore static power

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
    print("RESULTS - LOIHI 2 (estimated)")
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

    # Detect GPU type so we read/write the right metrics file
    metrics_path = get_metrics_path(_detect_gpu_type())

    # If GPU benchmark already exists, print savings immediately
    try:
        with open(metrics_path, 'r') as f:
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

    update_metrics_file('loihi_estimate', result, metrics_path)


def run_ops_estimate(num_steps=30):
    """
    Run all 5,000 dataset samples through the trained SNN and measure:
      - Actual spike rate per layer (replaces the assumed 10% in --loihi)
      - Real SOPs per inference (spike_rate × synapses × num_steps)
      - Per-class spike rate breakdown (shows input-dependent compute)
      - Loihi 2 energy estimate using measured (not assumed) spike rate
      - Total and per-sample inference time over the full dataset
    """
    print("\n" + "="*70)
    print("SNN OPS ESTIMATE - FULL DATASET")
    print("="*70)

    model, checkpoint = load_model_from_disk()
    model.eval()

    print(f"\nLoading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    cat_cols = ['time_of_day', 'event_category', 'scheduled_event',
                'location', 'weather', 'last_media']
    for col in cat_cols:
        df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    drop_cols    = ['suggestion_name', 'suggestion_label']
    feature_cols = [c for c in df.columns if c not in drop_cols]
    X_all        = torch.tensor(df[feature_cols].values, dtype=torch.float32)
    y_all        = df['suggestion_label'].values
    labels       = sorted(df['suggestion_name'].unique())
    num_samples  = len(X_all)
    print(f"  {num_samples} samples  |  {len(feature_cols)} features  |  {len(labels)} classes")

    input_size  = model.input_size
    hidden_size = model.hidden_size
    output_size = model.output_size
    synapses_l1 = input_size  * hidden_size   # 20 × 64  = 1,280
    synapses_l2 = hidden_size * output_size   # 64 × 23  = 1,472
    total_synapses = synapses_l1 + synapses_l2

    spikes_l1_per_sample = []   # fraction of hidden neurons that fired
    spikes_l2_per_sample = []   # fraction of output neurons that fired
    latencies_ms         = []
    per_class_spikes     = {label: [] for label in labels}

    print(f"\nRunning {num_samples} inference passes (num_steps={num_steps})...")

    with torch.no_grad():
        for i in range(num_samples):
            x = X_all[i].unsqueeze(0)   # shape (1, input_size)

            t0 = time.time()

            # Forward pass - capture intermediate spikes
            mem1 = model.lif1.init_leaky()
            mem2 = model.lif2.init_leaky()
            l1_spike_total = torch.zeros(hidden_size)
            l2_spike_total = torch.zeros(output_size)

            for _ in range(num_steps):
                cur1       = model.fc1(x)
                spk1, mem1 = model.lif1(cur1, mem1)
                cur2       = model.fc2(spk1)
                spk2, mem2 = model.lif2(cur2, mem2)
                l1_spike_total += spk1.squeeze(0)
                l2_spike_total += spk2.squeeze(0)

            latencies_ms.append((time.time() - t0) * 1000)

            # Spike rate = spikes fired / (neurons × timesteps)
            rate_l1 = l1_spike_total.sum().item() / (hidden_size * num_steps)
            rate_l2 = l2_spike_total.sum().item() / (output_size * num_steps)
            spikes_l1_per_sample.append(rate_l1)
            spikes_l2_per_sample.append(rate_l2)

            # Track per class
            class_name = labels[y_all[i]]
            per_class_spikes[class_name].append((rate_l1 + rate_l2) / 2)

    avg_rate_l1   = float(np.mean(spikes_l1_per_sample))
    avg_rate_l2   = float(np.mean(spikes_l2_per_sample))
    overall_rate  = (avg_rate_l1 + avg_rate_l2) / 2

    # Real SOPs using measured spike rate
    sops_l1 = avg_rate_l1 * synapses_l1 * num_steps
    sops_l2 = avg_rate_l2 * synapses_l2 * num_steps
    total_sops = sops_l1 + sops_l2

    avg_latency_ms   = float(np.mean(latencies_ms))
    total_latency_ms = float(np.sum(latencies_ms))

    # Loihi energy with measured spike rate
    ENERGY_PER_SOP_PJ = 3.0
    CORE_STATIC_W     = 0.001
    dynamic_energy_uJ = (total_sops * ENERGY_PER_SOP_PJ) / 1e6
    static_energy_uJ  = CORE_STATIC_W * (num_steps * 0.001) * 1e6
    total_energy_uJ   = dynamic_energy_uJ + static_energy_uJ
    daily_energy_wh   = total_energy_uJ * 86400 / 3.6e9

    # Per-class spike rate summary
    class_rates = {
        cls: float(np.mean(rates)) if rates else 0.0
        for cls, rates in per_class_spikes.items()
    }
    class_rates_sorted = sorted(class_rates.items(), key=lambda x: x[1])

    print("\n" + "="*70)
    print("RESULTS - SNN OPS ESTIMATE")
    print("="*70)
    print(f"  Architecture:           {input_size} → {hidden_size} → {output_size}")
    print(f"  Timesteps:              {num_steps}")
    print(f"  Samples measured:       {num_samples:,}")
    print()
    print(f"  SPIKE RATES (measured from data):")
    print(f"    Layer 1 (hidden):     {avg_rate_l1*100:.2f}%")
    print(f"    Layer 2 (output):     {avg_rate_l2*100:.2f}%")
    print(f"    Overall avg:          {overall_rate*100:.2f}%")
    print()
    print(f"  OPS PER INFERENCE (real SOPs):")
    print(f"    Layer 1:              {sops_l1:,.1f} SOPs")
    print(f"    Layer 2:              {sops_l2:,.1f} SOPs")
    print(f"    Total:                {total_sops:,.1f} SOPs")
    print()
    print(f"  LOIHI 2 ENERGY (measured spike rate):")
    print(f"    Dynamic energy:       {dynamic_energy_uJ:.6f} µJ")
    print(f"    Static energy:        {static_energy_uJ:.6f} µJ")
    print(f"    Total per inference:  {total_energy_uJ:.6f} µJ")
    print(f"    Daily (24/7):         {daily_energy_wh:.8f} Wh")
    print()
    print(f"  INFERENCE LATENCY (GPU/CPU, all {num_samples:,} samples):")
    print(f"    Avg per sample:       {avg_latency_ms:.3f} ms")
    print(f"    Total dataset:        {total_latency_ms:.1f} ms")
    print()
    print(f"  SPIKE RATE BY CLASS (input-dependent compute):")
    print(f"    {'Class':<35} Spike Rate")
    print(f"    {'-'*50}")
    for cls, rate in class_rates_sorted:
        bar = '█' * int(rate * 40)
        print(f"    {cls:<35} {rate*100:5.2f}%  {bar}")
    print("="*70)
    print(f"  NOTE: SOPs use measured spike rate ({overall_rate*100:.1f}%), not assumed 10%.")
    print(f"        Loihi 2 energy based on Intel published 3 pJ/SOP figure.")

    result = {
        'model_type':             'snn',
        'num_samples':            num_samples,
        'num_steps':              num_steps,
        'architecture':           f"{input_size}→{hidden_size}→{output_size}",
        'synapses_l1':            synapses_l1,
        'synapses_l2':            synapses_l2,
        'total_synapses':         total_synapses,
        'measured_spike_rate_l1': avg_rate_l1,
        'measured_spike_rate_l2': avg_rate_l2,
        'measured_spike_rate_overall': overall_rate,
        'sops_l1':                sops_l1,
        'sops_l2':                sops_l2,
        'total_sops':             total_sops,
        'loihi_dynamic_uJ':       dynamic_energy_uJ,
        'loihi_static_uJ':        static_energy_uJ,
        'loihi_total_uJ':         total_energy_uJ,
        'loihi_daily_wh':         daily_energy_wh,
        'avg_latency_ms':         avg_latency_ms,
        'total_latency_ms':       total_latency_ms,
        'per_class_spike_rates':  class_rates,
        'timestamp':              datetime.now().isoformat(),
    }

    metrics_path = get_metrics_path(_detect_gpu_type())
    update_metrics_file('ops_estimate', result, metrics_path)


# ============================================================
# Argparse entry point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="MiniOS Neuromorphic SNN - train, benchmark GPU, or estimate Loihi energy"
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
    group.add_argument(
        '--ops-estimate',
        action='store_true',
        dest='ops_estimate',
        help='Measure real SOPs and spike rates across full dataset (requires saved model)',
    )

    args = parser.parse_args()

    if args.train:
        run_train()
    elif args.benchmark_gpu:
        run_benchmark_gpu()
    elif args.loihi:
        run_loihi_estimate()
    elif args.ops_estimate:
        run_ops_estimate()


if __name__ == "__main__":
    main()