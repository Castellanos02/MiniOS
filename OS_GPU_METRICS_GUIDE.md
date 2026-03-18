# GPU Metrics Collection from Running OS

## 🎯 Overview

This system collects **real-time GPU metrics** while users interact with MiniOS, allowing you to create graphs showing SNN performance during actual usage.

**Metrics Collected from Running OS:**
- ✅ Accuracy (user accepts vs rejects)
- ✅ RAM usage
- ✅ GPU allocated memory
- ✅ GPU reserved memory
- ✅ Power consumption (Watts)
- ✅ Total energy (Watt-hours)
- ✅ Inference time per prediction
- ✅ GPU temperature
- ✅ Total inferences
- ✅ Accepts/Rejects ratio

---

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│         MiniOS (Running)             │
│                                      │
│  User → SNN Suggestion → Feedback   │
│           ↓                          │
│    GPU Metrics Collection            │
│           ↓                          │
│    Export to Serial/Log              │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│   Python Metrics Collector           │
│   (Running on Host PC)               │
│                                      │
│   Captures Metrics → JSON            │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│   Visualization & Graphing           │
│                                      │
│   Creates Publication-Ready Graphs   │
└──────────────────────────────────────┘
```

---

## 📦 Files Added

### In `kernel/`:
- `neuromorphic_assistant_gpu.c` - GPU-accelerated inference with metrics

### In `neuromorphic_assistant/`:
- `collect_os_metrics.py` - Metrics collector from running OS
- `GPU_TRAINING_GUIDE.md` - Complete setup guide

---

## 🚀 Setup & Usage

### Step 1: Build OS with GPU Metrics

**Edit `kernel/kernel_carplay.c`:**

```c
// Include GPU version instead of regular version
#include "neuromorphic_assistant_gpu.c"

// In kernel_main():
void kernel_main(multiboot_info_t* mbd, uint32_t magic) {
    // ... existing init ...
    
    // Initialize GPU-accelerated SNN
    na_metrics_init();
    
#if USE_GPU && GPU_TYPE_NVIDIA
    na_gpu_init_nvidia();
    draw_text("GPU: NVIDIA RTX 4060", 20, 3,
             (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
#elif USE_GPU && !GPU_TYPE_NVIDIA
    na_gpu_init_amd();
    draw_text("GPU: AMD RX 5500 XT", 20, 3,
             (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
#else
    draw_text("GPU: CPU Mode", 20, 3,
             (COLOR_BLACK << 4) | COLOR_YELLOW);
#endif
    
    // ... rest of init ...
}

// Replace ml_suggest_activity():
static uint8_t ml_suggest_activity(void) {
    return na_suggest_with_gpu(
        g_ml.current_hour,
        g_ml.current_minute,
        g_ml.energy_level,
        g_ml.engagement,
        g_ml.idle_cycles,
        g_metrics.total_accepts,  // Use tracked accepts
        g_metrics.total_rejects   // Use tracked rejects
    );
}

// In feedback handling:
if (key == 'y') {
    // User accepted
    na_metrics_record_feedback(1);  // Record accept
    
    draw_text("Learning from your choice...", 14, 17,
             (COLOR_LIGHT_GREEN << 4) | COLOR_WHITE);
    
    // Export metrics to serial
    na_metrics_export_to_serial();
}
else if (key == 'n') {
    // User rejected
    na_metrics_record_feedback(0);  // Record reject
    
    draw_text("Learning from feedback...", 14, 16,
             (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
    
    // Export metrics to serial
    na_metrics_export_to_serial();
}

// Add metrics display screen (optional)
void show_metrics_screen(void) {
    clear_screen();
    
    fill_box(0, 0, VGA_WIDTH, 1, (COLOR_BLUE << 4) | COLOR_WHITE);
    draw_text("MiniOS - SNN Performance Metrics", 10, 0,
             (COLOR_BLUE << 4) | COLOR_WHITE);
    
    // Draw metrics
    na_metrics_draw_stats(5, 2);
    
    fill_box(0, VGA_HEIGHT - 1, VGA_WIDTH, 1,
            (COLOR_DARK_GRAY << 4) | COLOR_LIGHT_GREEN);
    draw_text("B: Back  E: Export Metrics", 10, VGA_HEIGHT - 1,
             (COLOR_DARK_GRAY << 4) | COLOR_LIGHT_GREEN);
}
```

---

### Step 2: Configure GPU Type

**Edit `kernel/neuromorphic_assistant_gpu.c`:**

```c
// For NVIDIA RTX 4060:
#define USE_GPU 1
#define GPU_TYPE_NVIDIA 1

// For AMD RX 5500 XT:
#define USE_GPU 1
#define GPU_TYPE_NVIDIA 0  // AMD mode
```

---

### Step 3: Build with GPU Support

```bash
cd minios

# Build OS with GPU metrics
make clean
make iso-carplay
```

---

### Step 4: Run OS with Serial Output

**Option A: QEMU with serial output to file**

```bash
# Run QEMU and redirect serial to file
qemu-system-x86_64 -cdrom build/minios_carplay.iso \
    -m 256M \
    -serial file:os_metrics.log
```

**Option B: QEMU with serial to stdout**

```bash
qemu-system-x86_64 -cdrom build/minios_carplay.iso \
    -m 256M \
    -serial stdio > os_metrics.log
```

**Option C: Real hardware with serial cable**

```bash
# OS outputs to COM1/ttyS0
# Connect serial cable to PC
# Capture with: screen /dev/ttyUSB0 115200 > os_metrics.log
```

---

### Step 5: Collect Metrics (While OS Runs)

**Open a second terminal:**

```bash
cd minios/neuromorphic_assistant

# Collect from log file
python collect_os_metrics.py --mode collect --source file --logfile ../os_metrics.log

# OR collect from serial port
python collect_os_metrics.py --mode collect --source serial --port /dev/ttyUSB0

# Let it run while you interact with the OS
# Press Ctrl+C when done
```

**Output:**
```
📊 MiniOS Metrics Collector

Starting collection...
Press Ctrl+C to stop

✓ Monitoring log file: ../os_metrics.log
✓ Collected metrics: 1 samples
✓ Collected metrics: 2 samples
✓ Collected metrics: 3 samples
...
✓ Collected metrics: 50 samples

^C
Stopping collection...
✓ Metrics saved to: os_runtime_metrics.json
✓ Collected 50 samples
```

---

### Step 6: Create Graphs

```bash
# Generate comprehensive graphs
python collect_os_metrics.py --mode visualize \
    --output os_runtime_metrics.json \
    --graphs os_runtime_graphs.png
```

**Output:**
- `os_runtime_graphs.png` - 9-panel graph with all metrics
- Shows real user interaction data!

---

### Step 7 (Optional): Live Monitoring

```bash
# Watch metrics in real-time while OS runs
python collect_os_metrics.py --mode live --source file --logfile ../os_metrics.log
```

**Shows live updating graphs as users interact with OS!**

---

## 📊 Metrics Flow Example

**User Session:**

```
1. OS boots
   → Metrics initialized
   
2. User opens calendar at 08:50
   → SNN makes suggestion: "Workout"
   → Inference runs on GPU
   → Metrics recorded:
      - Inference time: 12 ms
      - GPU memory: 512 MB
      - Power: 85 W
   → Exported to serial

3. User presses 'Y' (accept)
   → Feedback recorded
   → Accuracy updated
   → Metrics exported:
      - Total accepts: 1
      - Accuracy: 100%

4. Next suggestion at 11:20
   → SNN suggests: "Quick break"
   → User presses 'N' (reject)
   → Metrics updated:
      - Total accepts: 1
      - Total rejects: 1
      - Accuracy: 50%
      
5. After 20 interactions
   → Comprehensive metrics collected
   → Energy consumption tracked
   → All data saved for graphing
```

---

## 📈 Graphs Generated

**9-Panel Comprehensive Visualization:**

1. **Real-Time Accuracy** - Improves as OS learns from user
2. **Cumulative Suggestions** - Total inferences over time
3. **Inference Latency** - Per-prediction time (ms)
4. **System Memory** - RAM usage
5. **GPU Memory** - Allocated memory
6. **GPU Power** - Instantaneous power draw
7. **Cumulative Energy** - Total energy consumption
8. **GPU Temperature** - Thermal monitoring
9. **Summary Statistics** - Final metrics

**Perfect for research papers!**

---

## 🔬 Experimental Scenarios

### Scenario 1: Compare GPU vs CPU

```bash
# Build with GPU
make clean && make iso-carplay
# Run and collect metrics
# Save as: nvidia_gpu_metrics.json

# Build without GPU (edit GPU_TYPE settings)
make clean && make iso-carplay
# Run and collect metrics
# Save as: cpu_only_metrics.json

# Compare
python -c "import json, matplotlib.pyplot as plt
nvidia = json.load(open('nvidia_gpu_metrics.json'))
cpu = json.load(open('cpu_only_metrics.json'))
# Create comparison graphs
"
```

---

### Scenario 2: Long-term Learning Study

```bash
# Run OS for 100 interactions
# Track accuracy improvement over time
# Measure energy cost of learning

python collect_os_metrics.py --mode collect --source file
# Interact with OS for 30 minutes
# Ctrl+C when done

python collect_os_metrics.py --mode visualize
# See how accuracy improves with user feedback!
```

---

### Scenario 3: Power Efficiency Analysis

```bash
# Collect metrics over extended session
# Calculate:
# - Energy per inference
# - Energy per learning update
# - Total energy cost
# - Compare to baseline CPU
```

---

## 📊 Data Format

**os_runtime_metrics.json:**

```json
{
  "collection_time": "2025-03-13T14:30:00",
  "num_samples": 50,
  "data": [
    {
      "timestamp": "2025-03-13T14:30:10",
      "total_inferences": 5,
      "total_accepts": 3,
      "total_rejects": 2,
      "accuracy": 60.0,
      "avg_inference_ms": 12,
      "min_inference_ms": 10,
      "max_inference_ms": 15,
      "ram_current_bytes": 1048576,
      "gpu_mem_allocated": 536870912,
      "gpu_mem_reserved": 2147483648,
      "gpu_power_watts": 85,
      "gpu_temp_c": 65,
      "energy_mwh": 142
    },
    // ... 49 more samples
  ]
}
```

---

## 🎯 Research Metrics You Can Calculate

**From collected data:**

1. **Learning Efficiency**
   - Accuracy improvement per interaction
   - Time to reach 80% accuracy
   - Energy cost per accuracy point gained

2. **Inference Performance**
   - Average/min/max latency
   - Latency distribution
   - GPU vs CPU speedup

3. **Energy Consumption**
   - Total energy per session
   - Energy per inference
   - Energy per learning update
   - Power efficiency (inferences per Wh)

4. **Memory Usage**
   - Peak RAM requirement
   - GPU memory utilization
   - Memory efficiency

5. **GPU Utilization**
   - Temperature trends
   - Power draw patterns
   - Memory bandwidth

---

## 💡 Tips

**For Clean Data:**
- Run OS in consistent environment
- Let OS stabilize before collecting metrics
- Perform same number of interactions per trial
- Average over multiple runs

**For Publication Graphs:**
- Collect 3-5 trials per condition
- Calculate mean ± standard deviation
- Use error bars in graphs
- Compare different configurations

**For Best Results:**
- Use actual GPU (not simulation)
- Run on real hardware when possible
- Collect over longer sessions (100+ interactions)
- Monitor thermal conditions

---

## 🔧 Troubleshooting

### No Metrics in Log File

**Check:**
```bash
# Verify OS is outputting to serial
cat os_metrics.log

# Should see:
# METRICS_START
# total_inferences=1
# ...
# METRICS_END
```

**Fix:** Verify QEMU serial redirection

---

### Metrics Not Parsing

**Check JSON format:**
```bash
python -c "import json; print(json.load(open('os_runtime_metrics.json')))"
```

---

### Live Monitor Not Updating

**Ensure collector thread is running:**
- Check log file is being written
- Verify file path is correct
- Try `--source serial` instead

---

## ✅ Complete Workflow Summary

```bash
# 1. Build OS with GPU metrics
cd minios
make clean && make iso-carplay

# 2. Run OS with serial output
qemu-system-x86_64 -cdrom build/minios_carplay.iso \
    -m 256M -serial file:os_metrics.log &

# 3. Collect metrics (in another terminal)
cd neuromorphic_assistant
python collect_os_metrics.py --mode collect --source file \
    --logfile ../os_metrics.log

# 4. Interact with OS
# - Accept/reject suggestions
# - Let it collect 50+ samples
# - Press Ctrl+C in collector when done

# 5. Generate graphs
python collect_os_metrics.py --mode visualize

# 6. Result!
# - os_runtime_graphs.png (comprehensive visualization)
# - os_runtime_metrics.json (raw data)
# - Ready for research paper!
```

---

**You can now collect GPU metrics from your running OS and create beautiful graphs!** 📊⚡🚀
