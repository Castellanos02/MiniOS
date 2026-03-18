# Complete HWiNFO64 + MiniOS Workflow Guide
## External AMD GPU Monitoring with OS Runtime Metrics

## 🎯 Overview

This workflow gives you **real GPU metrics** from your AMD RX 5500 XT while the OS runs, combined with OS interaction data.

**What you'll collect:**
- ✅ Real GPU power consumption (Watts)
- ✅ Real GPU temperature (°C)
- ✅ Real GPU memory usage (MB)
- ✅ Real GPU clock speeds
- ✅ OS accuracy (learns from user feedback)
- ✅ Inference latency
- ✅ User interaction patterns
- ✅ All time-synchronized and combined

**Perfect for research papers and analysis!**

---

## 📦 Prerequisites

### Step 1: Download HWiNFO64

```
https://www.hwinfo.com/download/

Download: HWiNFO64 Installer (free)
Install to default location
```

### Step 2: Install Python Dependencies

```bash
pip install pandas matplotlib numpy
```

### Step 3: Build Your OS

```bash
cd minios
make clean
make iso-carplay
```

---

## 🚀 Complete Workflow

### Phase 1: Setup HWiNFO64 Logging

#### 1. Open HWiNFO64

```
- Launch HWiNFO64
- Click "Sensors" button (or press F8)
- Sensors window opens
```

#### 2. Configure Logging

```
In Sensors window:
1. Click the "Logging" button (bottom toolbar)
2. Click "Configure..."

Configuration settings:
  ✓ Log Interval: 1000 ms (1 second)
  ✓ Separator: Comma
  ✓ File type: CSV
  ✓ Log file: C:\hwinfo_logs\os_session.csv
```

#### 3. Select Metrics to Log

**Find your AMD RX 5500 XT section** (scroll in sensors list)

**Select these metrics** (right-click → Log):
```
For AMD Radeon RX 5500 XT:
  ☑ GPU Power [W]
  ☑ GPU Temperature [°C]
  ☑ GPU Hot Spot Temperature [°C]
  ☑ GPU Memory Used [MB]
  ☑ GPU Core Clock [MHz]
  ☑ GPU Memory Clock [MHz]
  ☑ GPU Fan Speed [RPM]
  ☑ GPU Fan Speed [%]
```

**How to select:**
1. Find metric in list
2. Right-click on the value
3. Check "Log Value"
4. Green "L" appears next to metric

#### 4. Start Logging

```
1. Click "Start Logging" button
2. Choose save location
3. HWiNFO64 now logging every 1 second
4. Leave HWiNFO64 running in background
```

**Verify:**
- "Logging active" shown in status bar
- Log file growing in size

---

### Phase 2: Run MiniOS and Collect Metrics

#### Terminal 1: Run MiniOS

```bash
cd minios

# Run OS with serial output
qemu-system-x86_64 -cdrom build/minios_carplay.iso \
    -m 256M \
    -serial file:os_metrics.log
```

**OS boots and runs**

#### Terminal 2: Collect OS Metrics

```bash
# Open second terminal
cd minios/neuromorphic_assistant

# Start collecting
python collect_os_metrics.py --mode collect \
    --source file \
    --logfile ../os_metrics.log
```

**Expected output:**
```
📊 MiniOS Metrics Collector

Starting collection...
Press Ctrl+C to stop

✓ Monitoring log file: ../os_metrics.log
✓ Collected metrics: 1 samples
✓ Collected metrics: 2 samples
...
```

---

### Phase 3: Interact with OS

**Now interact with MiniOS for 5-10 minutes:**

1. **Wait for first notification** (08:50 in OS time)
   - Press `Y` to accept or `N` to reject
   
2. **Continue interacting**
   - Accept/reject suggestions
   - Let OS learn from your feedback
   - Do at least 20-30 interactions

3. **Watch both terminals:**
   - Terminal 1: OS running
   - Terminal 2: Metrics being collected
   - HWiNFO64: GPU metrics being logged

**Tips:**
- Make varied choices (some accept, some reject)
- Let OS run through multiple time periods
- More interactions = better learning data

---

### Phase 4: Stop Collection

#### 1. Stop OS Metrics Collection

```bash
# In Terminal 2 (collector)
Press Ctrl+C

Output:
✓ Metrics saved to: os_runtime_metrics.json
✓ Collected 47 samples
```

#### 2. Stop QEMU

```bash
# In Terminal 1 (QEMU)
Press Ctrl+C or close window
```

#### 3. Stop HWiNFO64 Logging

```
In HWiNFO64:
1. Click "Stop Logging" button
2. Note the save location
3. You can close HWiNFO64
```

**You now have:**
- `os_runtime_metrics.json` - OS interaction data
- `os_session.csv` - GPU hardware metrics from HWiNFO64

---

### Phase 5: Combine Metrics

```bash
cd minios/neuromorphic_assistant

# Combine HWiNFO64 + OS metrics
python combine_hwinfo_metrics.py \
    --hwinfo C:/hwinfo_logs/os_session.csv \
    --os os_runtime_metrics.json \
    --output combined_metrics.json \
    --graph combined_metrics_graph.png
```

**Expected output:**
```
📊 Combining HWiNFO64 + MiniOS Metrics

============================================================
Loading HWiNFO64 data from: C:/hwinfo_logs/os_session.csv
  Found 347 samples
  Columns: ['Date', 'Time', 'GPU Power [W]', ...]
  ✓ Found GPU power: GPU Power [W]
  ✓ Found GPU temp: GPU Temperature [°C]
  ✓ Found GPU memory: GPU Memory Used [MB]
  ✓ Parsed timestamps

Loading OS metrics from: os_runtime_metrics.json
  ✓ Found 47 OS samples

Correlating metrics (window: ±2.0s)...
  ✓ Matched 45/47 OS samples with HWiNFO64 data

✓ Combined metrics saved to: combined_metrics.json

============================================================
COMBINED METRICS SUMMARY
============================================================

GPU Power (Actual from HWiNFO64):
  Average: 118.3 W
  Min: 95.2 W
  Max: 132.7 W

GPU Temperature (Actual from HWiNFO64):
  Average: 68.4 °C
  Min: 62.0 °C
  Max: 74.5 °C

OS Metrics:
  Final Accuracy: 82.5%
  Total Samples: 45

Energy Consumption:
  Session duration: 8.3 minutes
  Total energy: 16.35 Wh

============================================================

✓ Visualization saved to: combined_metrics_graph.png

✓ Complete!

Files created:
  - combined_metrics.json (combined data)
  - combined_metrics_graph.png (visualization)
```

---

## 📊 What You Get

### combined_metrics.json

Complete dataset with all metrics:

```json
{
  "source": "combined_hwinfo64_and_os",
  "num_samples": 45,
  "data": [
    {
      "timestamp": "2025-03-13T14:32:15.123456",
      "total_inferences": 5,
      "total_accepts": 3,
      "total_rejects": 2,
      "accuracy": 60.0,
      "avg_inference_ms": 12,
      "gpu_power_watts_actual": 121.3,
      "gpu_temp_c_actual": 67.2,
      "gpu_memory_mb_actual": 542.1,
      "hwinfo_timestamp": "2025-03-13T14:32:15.000000",
      "time_diff_seconds": 0.123
    },
    // ... 44 more samples
  ]
}
```

### combined_metrics_graph.png

4-panel visualization:
1. **OS Learning Accuracy** - Shows improvement over time
2. **Inference Latency** - Per-prediction time
3. **GPU Power (HWiNFO64 Actual)** - Real power consumption
4. **GPU Temperature (HWiNFO64 Actual)** - Real thermal data

---

## 🔬 Analysis You Can Do

### 1. Energy Efficiency Analysis

```python
import json
import numpy as np

with open('combined_metrics.json', 'r') as f:
    data = json.load(f)

power = [m['gpu_power_watts_actual'] for m in data['data']]
accuracy = [m['accuracy'] for m in data['data']]

# Energy per accuracy point
avg_power = np.mean(power)
final_accuracy = accuracy[-1]
energy_per_accuracy = avg_power / final_accuracy

print(f"Energy efficiency: {energy_per_accuracy:.2f} W per accuracy point")
```

### 2. Thermal Performance

```python
temp = [m['gpu_temp_c_actual'] for m in data['data']]
power_samples = [m['gpu_power_watts_actual'] for m in data['data']]

import matplotlib.pyplot as plt

plt.scatter(power_samples, temp)
plt.xlabel('Power (W)')
plt.ylabel('Temperature (°C)')
plt.title('Power vs Temperature - AMD RX 5500 XT')
plt.grid(True)
plt.savefig('power_vs_temp.png')
```

### 3. Learning Dynamics

```python
accepts = []
rejects = []
accuracy_trend = []

for m in data['data']:
    accepts.append(m['total_accepts'])
    rejects.append(m['total_rejects'])
    accuracy_trend.append(m['accuracy'])

# Plot learning curve
plt.plot(accuracy_trend)
plt.xlabel('Interaction')
plt.ylabel('Accuracy (%)')
plt.title('SNN Learning Over Time')
plt.savefig('learning_curve.png')
```

---

## 📋 Checklist for Each Session

**Before starting:**
- [ ] HWiNFO64 installed
- [ ] Logging configured with GPU metrics selected
- [ ] OS built successfully
- [ ] Two terminals open

**During session:**
- [ ] HWiNFO64 logging started
- [ ] QEMU running OS
- [ ] Metrics collector running
- [ ] Interacting with OS (20+ times)

**After session:**
- [ ] Stop collector (Ctrl+C)
- [ ] Stop QEMU
- [ ] Stop HWiNFO64 logging
- [ ] Run combine script
- [ ] Verify output files created

---

## 🎯 Quick Reference Commands

```bash
# === SETUP (Once) ===
# 1. Download HWiNFO64
# 2. Configure logging in HWiNFO64
# 3. Build OS
cd minios && make clean && make iso-carplay

# === RUN SESSION ===
# Terminal 1: Run OS
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -serial file:os_metrics.log

# Terminal 2: Collect OS metrics
cd neuromorphic_assistant
python collect_os_metrics.py --mode collect --source file --logfile ../os_metrics.log

# HWiNFO64: Start logging

# === INTERACT ===
# Use OS, accept/reject suggestions (20+ times)

# === STOP ===
# Ctrl+C in Terminal 2
# Ctrl+C in Terminal 1 or close QEMU
# Stop logging in HWiNFO64

# === COMBINE ===
python combine_hwinfo_metrics.py \
    --hwinfo /path/to/hwinfo_log.csv \
    --os os_runtime_metrics.json

# === DONE ===
# combined_metrics.json - Full data
# combined_metrics_graph.png - Visualization
```

---

## 💡 Pro Tips

### Tip 1: Create HWiNFO64 Preset

Save your logging configuration:
```
In HWiNFO64:
- Configure metrics once
- File → Preferences → Logging
- Save configuration
- Next time: Just click "Start Logging"
```

### Tip 2: Automated Log Names

Use timestamp in filenames:
```bash
# In HWiNFO64, set log file to:
C:\hwinfo_logs\session_20250313_1430.csv

# Makes it easy to track multiple sessions
```

### Tip 3: Multiple Sessions

Run multiple sessions to average results:
```bash
# Session 1
# ... run and collect ...
mv combined_metrics.json session1_metrics.json

# Session 2
# ... run and collect ...
mv combined_metrics.json session2_metrics.json

# Session 3
# ... run and collect ...
mv combined_metrics.json session3_metrics.json

# Average results
python average_sessions.py session*.json
```

### Tip 4: Time Synchronization

Make sure clocks are synchronized:
```bash
# Check system time before starting
date

# HWiNFO64 uses system time
# Python uses system time
# Should match!
```

---

## 🐛 Troubleshooting

### Issue: HWiNFO64 columns not found

**Problem:** Script can't find GPU metrics in CSV

**Solution:**
```bash
# Check CSV column names
python -c "import pandas as pd; df = pd.read_csv('hwinfo_log.csv'); print(df.columns.tolist())"

# Update script if needed, or rename columns in CSV
```

### Issue: No metrics matched

**Problem:** Time correlation failed

**Solution:**
```bash
# Increase correlation window
python combine_hwinfo_metrics.py \
    --hwinfo hwinfo.csv \
    --os os_metrics.json \
    --window 5.0  # Increase from 2.0 to 5.0 seconds
```

### Issue: CSV import errors

**Problem:** HWiNFO64 CSV format issue

**Solution:**
```bash
# Check CSV encoding
file hwinfo_log.csv

# Try different encoding
# Edit combine_hwinfo_metrics.py, change:
# df = pd.read_csv(filepath, encoding='utf-8')
# to:
# df = pd.read_csv(filepath, encoding='latin1')
```

---

## 📊 Expected Results

### Typical Session (AMD RX 5500 XT)

```
Duration: 8-10 minutes
OS Interactions: 30-40
HWiNFO64 Samples: 480-600 (1 per second)
OS Samples: 30-40 (1 per interaction)
Matched: ~95% correlation

GPU Power:
  Idle: ~20-30W
  During inference: ~100-130W
  Average: ~110-120W

GPU Temperature:
  Start: ~50-60°C
  Running: ~65-75°C
  Average: ~68-72°C

GPU Memory:
  Model loaded: ~500-800MB
  
OS Accuracy:
  Initial: ~30-40%
  After 20 interactions: ~60-70%
  After 40 interactions: ~75-85%
```

---

## ✅ Success Indicators

**You'll know it worked when:**

1. ✅ HWiNFO64 CSV has GPU data
2. ✅ OS JSON has interaction data
3. ✅ Combine script matches >90% samples
4. ✅ Graph shows real power/temp curves
5. ✅ Power varies (not flat line)
6. ✅ Accuracy improves over time
7. ✅ Energy calculation makes sense

---

## 🎓 Research Metrics You Can Report

**From this data:**

1. **Energy per Inference:** Total energy ÷ total inferences
2. **Power Efficiency:** Accuracy improvement per Watt
3. **Thermal Stability:** Temperature variance during session
4. **Learning Efficiency:** Interactions needed to reach 80% accuracy
5. **Real-time Performance:** Actual inference latency distribution
6. **Hardware Utilization:** GPU memory vs model accuracy
7. **Energy Cost of Learning:** Energy used during accept vs reject

**Perfect for papers on:**
- Neuromorphic computing energy efficiency
- On-device learning costs
- Edge AI performance
- GPU acceleration for SNNs

---

## 🎯 Summary

**This workflow gives you:**
- ✅ Real GPU metrics (not estimates)
- ✅ OS learning data
- ✅ Time-synchronized
- ✅ Automated combination
- ✅ Research-quality data
- ✅ Works on Windows with AMD GPU

**Time investment:**
- Setup: 15 minutes (once)
- Each session: 10 minutes
- Analysis: 5 minutes

**Result:**
Publication-ready data showing real GPU performance with your neuromorphic OS! 🎉

---

**Ready to collect data? Follow the workflow above and you'll have complete metrics!** 🚀
