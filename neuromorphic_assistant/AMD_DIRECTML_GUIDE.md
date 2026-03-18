# AMD GPU Setup with DirectML on Windows

## 🎯 Problem

AMD GPUs on Windows don't work with standard ROCm monitoring tools. The solution is **DirectML** - Microsoft's DirectX Machine Learning API.

**Your GPU:** AMD Radeon RX 5500 XT  
**Platform:** Windows  
**Solution:** torch-directml

---

## 📦 Installation

### Step 1: Install DirectML

```bash
pip install torch-directml
```

### Step 2: Install Other Dependencies

```bash
pip install numpy lava-nc psutil matplotlib
```

---

## ✅ Verify DirectML Works

```python
import torch_directml

# Check if DirectML is available
if torch_directml.is_available():
    print(f"✓ DirectML is available!")
    print(f"  Devices: {torch_directml.device_count()}")
    print(f"  Device 0: {torch_directml.device_name(0)}")
    
    # Create a test tensor
    dml = torch_directml.device(0)
    x = torch.tensor([1.0, 2.0, 3.0]).to(dml)
    print(f"  Test tensor: {x}")
else:
    print("✗ DirectML not available")
```

**Expected output:**
```
✓ DirectML is available!
  Devices: 1
  Device 0: AMD Radeon RX 5500 XT
  Test tensor: tensor([1., 2., 3.], device='privateuseone:0')
```

---

## 🚀 Training with DirectML

### Use the DirectML Training Script

```bash
cd minios/neuromorphic_assistant

# Train with DirectML support
python train_with_directml.py
```

**What it does:**
1. Auto-detects AMD GPU via DirectML
2. Falls back to CPU if DirectML not available
3. Collects metrics (power estimated for AMD RX 5500 XT)
4. Works on Windows without ROCm

---

## 📊 Metrics Collection

### What You Get with DirectML

**Available:**
- ✅ GPU Detection (AMD Radeon RX 5500 XT)
- ✅ Training time
- ✅ RAM usage
- ✅ GPU memory (estimated from process)
- ✅ Power consumption (TDP estimate: 130W for RX 5500 XT)
- ✅ Energy calculation
- ✅ Accuracy tracking

**Not Available (DirectML limitations):**
- ⚠️ Real-time power monitoring (uses TDP estimate)
- ⚠️ GPU temperature (uses typical estimate)
- ⚠️ Detailed memory breakdown

**Why?** DirectML is a compute API, not a monitoring API. It doesn't expose hardware sensors like NVML does for NVIDIA.

---

## 🔬 Comparison: DirectML vs ROCm vs NVML

### NVIDIA (NVML)
```
✓ Real-time power monitoring
✓ Temperature monitoring
✓ Detailed memory info
✓ Fan speed, clock speeds
✓ Full hardware telemetry
```

### AMD on Linux (ROCm SMI)
```
✓ Real-time power monitoring
✓ Temperature monitoring
✓ Detailed memory info
✓ Clock speeds, voltages
✓ Full hardware telemetry
```

### AMD on Windows (DirectML)
```
✓ GPU compute access
✓ Basic device info
~ Memory estimation (via process)
~ Power estimation (via TDP)
~ Temperature estimation
✗ No direct hardware sensors
```

---

## 💡 Workarounds for Better Metrics

### Option 1: Use AMD Adrenalin Software

Run **AMD Radeon Software** in the background and monitor manually:

1. Open AMD Radeon Software
2. Go to Performance → Metrics
3. Enable overlay or logging
4. Train your model
5. Record metrics from AMD software

**Manual tracking:**
- GPU usage %
- VRAM usage
- Power draw
- Temperature
- Clock speeds

---

### Option 2: Use HWiNFO64

**HWiNFO64** is a Windows hardware monitoring tool that can log AMD GPU metrics:

```bash
# Download HWiNFO64
https://www.hwinfo.com/download/

# Enable logging:
# 1. Open HWiNFO64
# 2. Sensors → Logging → Start
# 3. Train model
# 4. Stop logging
# 5. Export CSV
```

**Metrics available:**
- GPU power consumption (actual)
- GPU temperature (actual)
- VRAM usage (actual)
- Clock speeds
- Fan speeds

---

### Option 3: Dual-Boot Linux for ROCm

For **full GPU monitoring**, use Linux with ROCm:

```bash
# Ubuntu with ROCm
sudo apt install rocm-smi

# Then use:
python train_with_gpu_metrics.py
# Full AMD monitoring via amdsmi!
```

---

## 🎯 Recommended Workflow

### For Quick Testing (Windows)

```bash
# Use DirectML - it works!
pip install torch-directml
python train_with_directml.py
```

**You get:**
- GPU acceleration ✅
- Basic metrics ✅
- Quick and easy ✅

---

### For Full Metrics (Windows)

```bash
# 1. Start HWiNFO64 logging
# 2. Train model
python train_with_directml.py

# 3. Stop HWiNFO64 logging
# 4. Export CSV from HWiNFO64
# 5. Combine data:
#    - training_metrics.json (from Python)
#    - hwinfo_log.csv (from HWiNFO64)
```

---

### For Research (Linux)

```bash
# Boot into Linux
# Install ROCm
sudo apt install rocm-smi amdsmi

# Full monitoring
pip install amdsmi numpy lava-nc psutil matplotlib
python train_with_gpu_metrics.py
```

**You get:**
- Real-time power ✅
- Real temperature ✅
- Full metrics ✅

---

## 📈 Expected Performance: AMD RX 5500 XT

### Specifications
```
GPU: AMD Radeon RX 5500 XT
VRAM: 4GB or 8GB GDDR6
TDP: 130W
Compute Units: 22
Stream Processors: 1408
```

### Training Performance (Estimated)
```
Training time: ~70-90 seconds (15 epochs)
Power draw: ~100-130W (gaming/compute load)
Temperature: ~65-75°C
VRAM usage: ~500-800 MB (for SNN model)
```

### Comparison to NVIDIA RTX 4060
```
RTX 4060:     ~50-70s, ~85W, ~65°C
RX 5500 XT:   ~70-90s, ~120W, ~70°C

RX 5500 XT is slightly slower, uses more power
But still fully capable for SNN training!
```

---

## 🐛 Troubleshooting

### DirectML Not Detecting GPU

**Check drivers:**
```bash
# Update AMD drivers
# Download from: https://www.amd.com/en/support

# After update, restart and test:
python -c "import torch_directml; print(torch_directml.is_available())"
```

---

### Training Still Uses CPU

**Verify DirectML installation:**
```bash
pip show torch-directml
# Should show version info

# Reinstall if needed:
pip uninstall torch-directml
pip install torch-directml
```

---

### Import Errors

**Full clean install:**
```bash
pip uninstall torch torch-directml
pip install torch-directml
```

---

## 📊 Example Output with DirectML

```
GPU-ACCELERATED SNN TRAINING - DirectML Support for AMD
======================================================================
Checking GPU support...

✓ DirectML available - 1 device(s)
  Device 0: AMD Radeon RX 5500 XT

Configuration:
  GPU Type: amd_directml
  Hidden neurons: 32
  Timesteps: 30
  Training samples: 100
  Epochs: 15
  Learning rate: 0.02

Training with GPU monitoring...
----------------------------------------------------------------------
Epoch  Loss       Acc%     Time(s)  Power(W)   Energy(Wh)   RAM(MB)    GPU(MB)
----------------------------------------------------------------------
1      0.4523     42.0     5.2      130.0      0.0188       1124.5     612.3
5      0.2134     75.0     26.1     130.0      0.0942       1135.1     618.4
10     0.1456     84.0     52.3     130.0      0.1889       1142.3     619.8
15     0.1123     88.0     78.5     130.0      0.2836       1145.2     620.1
----------------------------------------------------------------------

Training Summary:
  GPU Type: amd_directml
  Total time: 78.5 seconds
  Total energy: 0.2836 Wh
  Final accuracy: 88.0%
  Average power: 130.0 W (TDP estimate)
  Peak RAM: 1145.2 MB
  Peak GPU memory: 620.1 MB

✓ Metrics saved to: training_metrics.json
✓ Model saved to: minios_activity_model.npz

✓ Training complete!
```

---

## ✅ Summary

**For AMD RX 5500 XT on Windows:**

1. **Install DirectML:**
   ```bash
   pip install torch-directml
   ```

2. **Use DirectML training script:**
   ```bash
   python train_with_directml.py
   ```

3. **You get:**
   - ✅ GPU acceleration
   - ✅ Training works
   - ✅ Basic metrics
   - ~ Power estimated (130W TDP)
   - ~ Temperature estimated (65°C typical)

4. **For full metrics:**
   - Use HWiNFO64 alongside training
   - Or dual-boot Linux for ROCm

---

## 🎯 Quick Start Commands

```bash
# Install
pip install torch-directml numpy lava-nc psutil matplotlib

# Verify
python -c "import torch_directml; print(torch_directml.device_name(0))"

# Train
cd minios/neuromorphic_assistant
python train_with_directml.py

# Export
python export_to_minios.py

# Build OS
cd .. && make clean && make iso-carplay && make run-carplay
```

**Your AMD GPU will now be used for training!** 🚀

---

## 📝 Notes

- DirectML works for **compute** (training)
- Metrics are **estimated** (power, temp)
- For **research-grade metrics**, use HWiNFO64 or Linux
- For **just getting it working**, DirectML is perfect!

**Bottom line:** DirectML gets your AMD GPU working on Windows, even if metrics aren't as detailed as NVIDIA. The model will train faster than CPU! ⚡
