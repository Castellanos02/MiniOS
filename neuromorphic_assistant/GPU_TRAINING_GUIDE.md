# GPU Training and Metrics Collection Guide

## 🎯 Overview

This system collects comprehensive metrics during SNN training:

**Metrics Collected:**
- ✅ **Accuracy** - Model performance over epochs
- ✅ **RAM** - System memory usage
- ✅ **GPU Allocated Memory** - Active GPU memory
- ✅ **GPU Reserved Memory** - Total GPU memory
- ✅ **Power** - Instantaneous power draw (Watts)
- ✅ **Total Watt-Hours** - Cumulative energy consumption
- ✅ **Total Time** - Training duration
- ✅ **Inference Time** - Per-prediction latency

---

## 🖥️ GPU Support

### Your GPUs:

**NVIDIA GeForce RTX 4060**
- Driver: Latest NVIDIA drivers
- Monitoring: `nvidia-ml-py3` (pynvml)
- CUDA support: Yes

**AMD Radeon RX 5500 XT**
- Driver: AMD ROCm
- Monitoring: `amdsmi`
- ROCm support: Yes

---

## 📦 Installation

### For NVIDIA RTX 4060:

```bash
# Install NVIDIA monitoring
pip install nvidia-ml-py3

# Install other dependencies
pip install numpy lava-nc psutil matplotlib
```

### For AMD RX 5500 XT:

```bash
# Install ROCm (if not already installed)
# Follow: https://rocm.docs.amd.com/en/latest/deploy/linux/quick_start.html

# Install AMD monitoring
pip install amdsmi

# Install other dependencies
pip install numpy lava-nc psutil matplotlib
```

### Common Dependencies:

```bash
pip install numpy lava-nc psutil matplotlib
```

---

## 🚀 Usage

### Step 1: Run GPU-Monitored Training

```bash
cd minios/neuromorphic_assistant

# Train with GPU monitoring
python train_with_gpu_metrics.py
```

**Output:**
```
GPU-ACCELERATED SNN TRAINING WITH METRICS COLLECTION
======================================================================
✓ Detected NVIDIA GPU: NVIDIA GeForce RTX 4060

Configuration:
  Hidden neurons: 32
  Timesteps: 30
  Training samples: 100
  Epochs: 15
  Learning rate: 0.02

Training with GPU monitoring...
----------------------------------------------------------------------
Epoch  Loss       Acc%     Time(s)  Power(W)   Energy(Wh)   RAM(MB)    GPU(MB)
----------------------------------------------------------------------
1      0.4523     42.0     4.2      85.3       0.0100       1024.5     512.3
2      0.3621     58.0     8.5      87.1       0.0205       1028.2     515.1
3      0.2845     68.0     12.8     86.8       0.0310       1030.4     516.8
...
15     0.1123     88.0     63.5     85.5       0.1502       1045.2     520.1
----------------------------------------------------------------------

Training Summary:
  Total time: 63.5 seconds
  Total energy: 0.1502 Wh
  Final accuracy: 88.0%
  Average power: 86.1 W
  Peak RAM: 1045.2 MB
  Peak GPU memory: 520.1 MB
  GPU type: nvidia

✓ Metrics saved to: training_metrics.json
✓ Model saved to: minios_activity_model.npz

INFERENCE PERFORMANCE TEST
======================================================================
Running 100 inference tests...

Inference Performance:
  Average: 12.34 ms
  Min: 10.21 ms
  Max: 15.67 ms
  Std Dev: 1.23 ms

✓ Inference metrics saved to: inference_metrics.json
```

---

### Step 2: Visualize Metrics

```bash
# Create graphs
python visualize_metrics.py
```

**This creates:**
- `snn_training_metrics.png` - Comprehensive 9-panel visualization
- `training_metrics.csv` - Data in CSV format

**Graphs include:**
1. Accuracy over time
2. Loss over time
3. RAM usage
4. GPU memory (allocated vs reserved)
5. Power consumption
6. Cumulative energy
7. Training time
8. Inference time distribution
9. Summary statistics

---

### Step 3: Compare GPUs (Optional)

To compare NVIDIA vs AMD:

```bash
# Train on NVIDIA
python train_with_gpu_metrics.py
mv training_metrics.json nvidia_metrics.json

# Train on AMD (switch GPU)
python train_with_gpu_metrics.py
mv training_metrics.json amd_metrics.json

# Compare
python -c "from visualize_metrics import create_comparison_plots; create_comparison_plots('nvidia_metrics.json', 'amd_metrics.json')"
```

---

## 📊 Output Files

**JSON Files:**
- `training_metrics.json` - Complete training metrics
- `inference_metrics.json` - Inference performance data

**Graphics:**
- `snn_training_metrics.png` - All metrics visualized
- `gpu_comparison.png` - GPU comparison (if comparing)

**Data:**
- `training_metrics.csv` - Metrics in CSV format
- `minios_activity_model.npz` - Trained model weights

---

## 🔍 Metrics Explanation

### 1. Accuracy
- **What:** % of correct predictions on training data
- **Goal:** Higher is better (target: 80-90%)
- **Graph:** Line plot over epochs

### 2. Loss
- **What:** Training loss (policy gradient)
- **Goal:** Lower is better
- **Graph:** Line plot over epochs

### 3. RAM (System Memory)
- **What:** Python process memory usage
- **Unit:** Megabytes (MB)
- **Graph:** Line plot over epochs

### 4. GPU Allocated Memory
- **What:** Active GPU memory in use
- **Unit:** Megabytes (MB)
- **Graph:** Line plot over epochs (vs reserved)

### 5. GPU Reserved Memory
- **What:** Total GPU memory allocated to process
- **Unit:** Megabytes (MB)
- **Graph:** Line plot over epochs (vs allocated)

### 6. Power
- **What:** Instantaneous GPU power draw
- **Unit:** Watts (W)
- **Source:** GPU sensors
- **Graph:** Line plot over epochs

### 7. Energy (Watt-Hours)
- **What:** Cumulative energy consumed
- **Unit:** Watt-hours (Wh)
- **Formula:** ∫ Power × Time
- **Graph:** Line plot over epochs

### 8. Total Time
- **What:** Elapsed training time
- **Unit:** Seconds
- **Graph:** Line plot over epochs

### 9. Inference Time
- **What:** Time per prediction
- **Unit:** Milliseconds (ms)
- **Graph:** Histogram distribution

---

## 🎛️ Configuration Options

Edit `train_with_gpu_metrics.py` to adjust:

```python
assistant, monitor = train_with_gpu_monitoring(
    num_epochs=15,          # Number of training epochs
    lr=0.02,                # Learning rate
    num_samples=100,        # Training samples per epoch
    hidden_size=32,         # Hidden layer neurons
    timesteps=30,           # SNN timesteps
)
```

**Trade-offs:**
- **More epochs:** Better accuracy, longer time, more energy
- **More timesteps:** More accurate spikes, slower training
- **Larger hidden:** More capacity, more memory, slower
- **More samples:** Better generalization, longer time

---

## 🔬 Experimental Comparisons

### Compare Different Configurations:

```bash
# Baseline
python train_with_gpu_metrics.py
mv training_metrics.json baseline_metrics.json

# Larger model
# Edit: hidden_size=64
python train_with_gpu_metrics.py
mv training_metrics.json large_model_metrics.json

# More timesteps
# Edit: timesteps=50
python train_with_gpu_metrics.py
mv training_metrics.json long_timesteps_metrics.json
```

---

## 📈 Expected Results

### NVIDIA RTX 4060:
```
Average power: 80-100 W
Peak GPU memory: 500-800 MB
Training time (15 epochs): 50-70 seconds
Inference time: 10-15 ms
```

### AMD RX 5500 XT:
```
Average power: 90-120 W
Peak GPU memory: 400-700 MB
Training time (15 epochs): 60-90 seconds
Inference time: 12-18 ms
```

---

## 🐛 Troubleshooting

### NVIDIA GPU Not Detected

```bash
# Check drivers
nvidia-smi

# Install monitoring
pip install nvidia-ml-py3

# Test
python -c "import pynvml; pynvml.nvmlInit(); print('OK')"
```

### AMD GPU Not Detected

```bash
# Check ROCm
rocm-smi

# Install monitoring
pip install amdsmi

# Test
python -c "import amdsmi; amdsmi.amdsmi_init(); print('OK')"
```

### No GPU Detected

The script will still work on CPU but won't collect GPU metrics:
```
⚠ No GPU detected - using CPU only
```

---

## 📝 Data Format

### training_metrics.json Structure:

```json
{
  "summary": {
    "total_time_seconds": 63.5,
    "total_energy_wh": 0.1502,
    "final_accuracy": 88.0,
    "average_power_watts": 86.1,
    "max_ram_mb": 1045.2,
    "max_gpu_allocated_mb": 520.1,
    "gpu_type": "nvidia"
  },
  "history": [
    {
      "epoch": 1,
      "accuracy": 42.0,
      "loss": 0.4523,
      "time_seconds": 4.2,
      "ram_mb": 1024.5,
      "gpu_allocated_mb": 512.3,
      "gpu_reserved_mb": 2048.0,
      "power_watts": 85.3,
      "energy_wh": 0.0100,
      "timestamp": "2025-03-13T10:30:45.123456"
    },
    ...
  ]
}
```

---

## 🎯 Next Steps

After collecting metrics:

1. **Visualize:** `python visualize_metrics.py`
2. **Export model:** `python export_to_minios.py`
3. **Build OS:** `cd .. && make iso-carplay`
4. **Run:** `make run-carplay`

---

## 💡 Tips

**For Best GPU Utilization:**
- Use larger batch sizes (more samples)
- Increase timesteps (more computation)
- Use larger hidden layers

**For Energy Efficiency:**
- Reduce timesteps
- Use smaller models
- Train for fewer epochs

**For Speed:**
- Reduce all parameters
- Use GPU (not CPU)
- Close other applications

---

**You now have complete GPU monitoring for your SNN training!** 📊⚡

---

## 🔧 AMD GPU on Windows: DirectML Solution

### Problem
AMD GPUs on Windows don't work with ROCm monitoring tools (amdsmi).

### Solution
Use **DirectML** (Microsoft's DirectX Machine Learning):

```bash
pip install torch-directml
```

### Usage

```bash
# Use DirectML training script
python train_with_directml.py
```

**This will:**
- ✅ Detect AMD GPU automatically
- ✅ Use GPU for acceleration
- ✅ Collect metrics (power estimated)
- ✅ Work on Windows without ROCm

### Limitations

DirectML provides **compute** but not full **monitoring**:
- ✅ GPU acceleration
- ✅ Training time
- ✅ Memory usage (estimated)
- ~ Power (TDP estimate: 130W for RX 5500 XT)
- ~ Temperature (typical estimate: 65°C)
- ✗ Real-time power sensors
- ✗ Real-time temperature sensors

### For Full Metrics on Windows

Use **HWiNFO64** alongside training:
1. Download HWiNFO64 (free)
2. Enable sensor logging
3. Run `python train_with_directml.py`
4. Stop logging and export CSV
5. Combine with training_metrics.json

### For Full Metrics on Linux

Use ROCm with amdsmi:
```bash
pip install amdsmi
python train_with_gpu_metrics.py
```

**See AMD_DIRECTML_GUIDE.md for complete setup!**

