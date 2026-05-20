#!/usr/bin/env python3
"""
Train DNN Baseline on Real Use Cases
Standard feedforward neural network (ReLU activations) trained on the same
dataset, split, and hyperparameters as the SNN for a fair comparison.

Usage:
    python train_usecase_dnn.py --train          # Train and save model
"""

import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
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

MODEL_PATH = 'minios_usecase_dnn_model.pth'


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
        'nvidia':        'usecase_training_metrics_dnn_nvidia.json',
        'nvidia_cuda':   'usecase_training_metrics_dnn_nvidia.json',
        'amd_directml':  'usecase_training_metrics_dnn_amd.json',
        'cpu':           'usecase_training_metrics_dnn_cpu.json',
    }
    return mapping.get(gpu_type, f'usecase_training_metrics_dnn_{gpu_type}.json')

class ActivityDNN(nn.Module):
    """
    Standard feedforward DNN - same topology as the SNN (input → 64 hidden → output)
    but uses ReLU activations and a single dense forward pass instead of LIF spiking
    neurons over multiple timesteps.
    """
    def __init__(self, input_size, hidden_size=64, output_size=10, dropout=0.25):
        super().__init__()

        self.input_size  = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_size, output_size),
        )

    def forward(self, x):
        return self.network(x)

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

        if epoch > 1 and self.history:
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
            'total_energy_wh':      sum(h['energy_wh'] for h in self.history),
            'total_time_seconds':   self.history[-1]['time_seconds'],
            'gpu_type':             self.gpu_type,
        }

    def cleanup(self):
        if self.nvml:
            try:
                self.nvml.nvmlShutdown()
            except:
                pass


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
    print("DNN BASELINE - DRIVING ASSISTANT TRAINING")
    print("="*70)

    monitor = GPUMonitor()

    print(f"\nLoading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    print(f"  Loaded {len(df)} rows  |  {df['suggestion_name'].nunique()} classes")

    # Encode categorical columns - identical to SNN script
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

    # 70-20-10 split - same random_state as SNN for identical splits
    X_tr, X_te, y_tr, y_te = train_test_split(X_all, y_all, test_size=0.10, random_state=42, stratify=y_all)
    X_tr, X_va, y_tr, y_va = train_test_split(X_tr,  y_tr,  test_size=0.222, random_state=42, stratify=y_tr)
    print(f"  Split (70-20-10):  train={len(X_tr)}  val={len(X_va)}  test={len(X_te)}")

    # Normalise - fit on train only
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

    model = ActivityDNN(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
    ).to(monitor.device)

    with torch.no_grad():
        nn.init.xavier_uniform_(model.network[0].weight)
        nn.init.xavier_uniform_(model.network[3].weight)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=num_epochs, eta_min=1e-4
    )

    monitor.start_monitoring()
    print(f"\nTraining {num_epochs} epochs...")
    print("="*70)

    best_accuracy       = 0
    best_model_state    = None
    early_stop_patience = 30
    epochs_no_improve   = 0

    for epoch in range(num_epochs):
        model.train()
        epoch_loss = epoch_correct = epoch_total = 0

        for X_batch, y_batch in loader:
            X_batch = X_batch.to(monitor.device)
            y_batch = y_batch.to(monitor.device)

            optimizer.zero_grad()
            logits = model(X_batch)
            loss   = F.cross_entropy(logits, y_batch, weight=class_weights)
            loss.backward()
            optimizer.step()

            with torch.no_grad():
                _, predicted  = logits.max(1)
                epoch_correct += (predicted == y_batch).sum().item()
                epoch_total   += y_batch.size(0)
                epoch_loss    += loss.item() * y_batch.size(0)

        scheduler.step()

        accuracy = (epoch_correct / epoch_total) * 100
        avg_loss = epoch_loss / epoch_total

        # Validation pass
        model.eval()
        val_correct = val_total = 0
        val_loss_sum = 0.0
        with torch.no_grad():
            for Xv, yv in val_loader:
                Xv, yv   = Xv.to(monitor.device), yv.to(monitor.device)
                logits_v = model(Xv)
                v_loss   = F.cross_entropy(logits_v, yv, weight=class_weights)
                _, pred_v = logits_v.max(1)
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

        print(f"Epoch {epoch+1:3d}/{num_epochs}  "
              f"loss={avg_loss:.4f}  train_acc={accuracy:5.1f}%  "
              f"val_acc={val_accuracy:5.1f}%  "
              f"best_val={best_accuracy:5.1f}%  "
              f"t={metrics['time_seconds']:.1f}s")


    if best_model_state:
        model.load_state_dict(best_model_state)
        print(f"\n  Best val weights restored  (val_acc: {best_accuracy:.1f}%)")

    # Test-set evaluation
    model.eval()
    test_correct = test_total = 0
    test_loader  = DataLoader(TensorDataset(X_test, y_test), batch_size=batch_size)

    # Measure inference latency over 100 passes on a single sample
    single_x = X_test[:1].to(monitor.device)
    latency_times = []
    with torch.no_grad():
        for _ in range(10):                         # warmup
            model(single_x)
        for _ in range(100):
            t0 = time.time()
            model(single_x)
            latency_times.append((time.time() - t0) * 1000)

    avg_inference_ms = float(np.mean(latency_times))
    p95_inference_ms = float(np.percentile(latency_times, 95))

    with torch.no_grad():
        for Xt, yt in test_loader:
            Xt, yt = Xt.to(monitor.device), yt.to(monitor.device)
            _, pred_t = model(Xt).max(1)
            test_correct += (pred_t == yt).sum().item()
            test_total   += yt.size(0)
    test_accuracy = (test_correct / test_total) * 100
    print(f"  Test-set accuracy:    {test_accuracy:.1f}%")
    print(f"  Avg inference:        {avg_inference_ms:.3f} ms")
    print(f"  p95 inference:        {p95_inference_ms:.3f} ms")

    # Save model
    torch.save({
        'model_state_dict':  model.state_dict(),
        'input_size':        model.input_size,
        'hidden_size':       model.hidden_size,
        'output_size':       model.output_size,
        'suggestion_labels': suggestion_labels,
        'dataset_path':      DATASET_PATH,
        'best_val_accuracy': best_accuracy,
        'test_accuracy':     test_accuracy,
        'split_mode':        '70-20-10',
        'num_samples':       len(df),
    }, MODEL_PATH)
    print(f"  Model saved to {MODEL_PATH}")

    # Save metrics
    metrics_path = get_metrics_path(monitor.gpu_type)
    summary = monitor.get_summary()
    summary['test_accuracy']     = test_accuracy
    summary['dataset_path']      = DATASET_PATH
    summary['model_type']        = 'dnn'
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


def load_dnn_from_disk():
    """Load saved DNN model. Exits with a clear message if not found."""
    try:
        checkpoint = torch.load(MODEL_PATH, map_location='cpu')
    except FileNotFoundError:
        print(f"\nModel file '{MODEL_PATH}' not found.")
        print(f"Run  python train_usecase_dnn.py --train  first.")
        raise SystemExit(1)

    model = ActivityDNN(
        input_size=checkpoint['input_size'],
        hidden_size=checkpoint['hidden_size'],
        output_size=checkpoint['output_size'],
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    print(f"Loaded model from {MODEL_PATH}")
    print(f"  Architecture:  {checkpoint['input_size']} → "
          f"{checkpoint['hidden_size']} → {checkpoint['output_size']}")
    return model, checkpoint


def run_ops_estimate():
    """
    Run all 5,000 dataset samples through the trained DNN and measure:
      - MACs per inference (fixed - always input×hidden + hidden×output)
      - Total MACs across the full dataset
      - Per-sample and total inference latency
      - MACs are the same for every input - proving always-on cost
    """
    print("\n" + "="*70)
    print("DNN OPS ESTIMATE - FULL DATASET")
    print("="*70)

    model, checkpoint = load_dnn_from_disk()
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

    # MACs are fixed regardless of input or output
    # Every Linear layer: MACs = in_features × out_features
    macs_l1 = input_size  * hidden_size   # 20 × 64 = 1,280
    macs_l2 = hidden_size * output_size   # 64 × 23 = 1,472
    macs_per_inference = macs_l1 + macs_l2
    total_macs = macs_per_inference * num_samples

    latencies_ms = []
    print(f"\nRunning {num_samples} inference passes...")

    with torch.no_grad():
        for i in range(num_samples):
            x  = X_all[i].unsqueeze(0)
            t0 = time.time()
            model(x)
            latencies_ms.append((time.time() - t0) * 1000)

    avg_latency_ms   = float(np.mean(latencies_ms))
    total_latency_ms = float(np.sum(latencies_ms))

    # Per-class breakdown - MACs are identical for every class (key point)
    per_class_macs = {label: macs_per_inference for label in labels}

    print("\n" + "="*70)
    print("RESULTS - DNN OPS ESTIMATE")
    print("="*70)
    print(f"  Architecture:           {input_size} → {hidden_size} → {output_size}")
    print(f"  Samples measured:       {num_samples:,}")
    print()
    print(f"  MACs PER INFERENCE (fixed, input-independent):")
    print(f"    Layer 1:              {macs_l1:,} MACs")
    print(f"    Layer 2:              {macs_l2:,} MACs")
    print(f"    Total per inference:  {macs_per_inference:,} MACs  ← always, every input")
    print(f"    Total dataset:        {total_macs:,} MACs")
    print()
    print(f"  INFERENCE LATENCY (all {num_samples:,} samples):")
    print(f"    Avg per sample:       {avg_latency_ms:.3f} ms")
    print(f"    Total dataset:        {total_latency_ms:.1f} ms")
    print()
    print(f"  MACs BY CLASS (input-independent compute):")
    print(f"    {'Class':<35} MACs")
    print(f"    {'-'*50}")
    for label in sorted(labels):
        print(f"    {label:<35} {macs_per_inference:,}  ← identical for all classes")
    print("="*70)
    print(f"  NOTE: DNN performs {macs_per_inference:,} MACs on every single inference,")
    print(f"        regardless of input values, time of day, or activity class.")
    print(f"        There is no sparsity, no threshold, no idle computation.")

    result = {
        'model_type':            'dnn',
        'num_samples':           num_samples,
        'architecture':          f"{input_size}→{hidden_size}→{output_size}",
        'macs_layer1':           macs_l1,
        'macs_layer2':           macs_l2,
        'macs_per_inference':    macs_per_inference,
        'total_macs_dataset':    total_macs,
        'spike_rate':            None,   # not applicable - included for compare script alignment
        'avg_latency_ms':        avg_latency_ms,
        'total_latency_ms':      total_latency_ms,
        'per_class_macs':        per_class_macs,
        'timestamp':             datetime.now().isoformat(),
    }

    metrics_path = get_metrics_path(_detect_gpu_type())
    update_metrics_file('ops_estimate', result, metrics_path)


def main():
    parser = argparse.ArgumentParser(
        description="MiniOS DNN Baseline - train a standard feedforward network for SNN comparison"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--train',
        action='store_true',
        help='Train the DNN and save model to minios_usecase_dnn_model.pth',
    )
    group.add_argument(
        '--ops-estimate',
        action='store_true',
        dest='ops_estimate',
        help='Measure MACs per inference across full dataset (requires saved model)',
    )

    parser.add_argument('--epochs',      type=int,   default=200,   help='Number of training epochs (default: 200)')
    parser.add_argument('--hidden-size', type=int,   default=64,    help='Hidden layer size (default: 64, matches SNN)')
    parser.add_argument('--batch-size',  type=int,   default=32,    help='Batch size (default: 32)')
    parser.add_argument('--lr',          type=float, default=0.001, help='Learning rate (default: 0.001)')

    args = parser.parse_args()

    if args.train:
        run_train(
            num_epochs=args.epochs,
            hidden_size=args.hidden_size,
            batch_size=args.batch_size,
            lr=args.lr,
        )
    elif args.ops_estimate:
        run_ops_estimate()


if __name__ == "__main__":
    main()