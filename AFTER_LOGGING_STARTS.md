# Complete Steps After Starting HWiNFO64 Logging

## 🎯 Current Status

✅ HWiNFO64 configured with GPU metrics
✅ Ready to start logging

---

## 📋 Complete Workflow (3 Terminals)

### **Terminal 1: HWiNFO64** (You're here!)

**Step 1: Start Logging**
```
1. Click "OK" in settings window
2. Click "Logging Start" button (bottom toolbar)
3. Save dialog appears
4. Choose location: C:\hwinfo_logs\session_1.csv
5. Click Save
6. Logging active! ✓
```

**Step 2: Minimize HWiNFO64**
```
Minimize the window (keep it running in background)
Logging will continue automatically
```

---

### **Terminal 2: Run MiniOS**

**Step 3: Open PowerShell/Command Prompt**

**Navigate to your project:**
```bash
cd C:\path\to\minios
# Replace with your actual path
```

**Step 4: Run QEMU with Serial Output**
```bash
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -serial file:os_metrics.log
```

**What happens:**
- QEMU window opens
- Your OS boots
- Serial output saves to `os_metrics.log`
- Leave this window open!

---

### **Terminal 3: Start OS Metrics Collector**

**Step 5: Open Another PowerShell/Command Prompt**

**Navigate to neuromorphic_assistant:**
```bash
cd C:\path\to\minios\neuromorphic_assistant
```

**Step 6: Start Collector**
```bash
python collect_os_metrics.py --mode collect --source file --logfile ..\os_metrics.log
```

**Expected output:**
```
📊 MiniOS Metrics Collector

Starting collection...
Press Ctrl+C to stop

✓ Monitoring log file: ..\os_metrics.log
```

**Leave this running!**

---

## 🎮 Interact with Your OS (10-15 Minutes)

**In the QEMU window:**

### **1. OS Boots**
```
╔═══════════════════════════════════════╗
║ MiniOS CarPlay                       ║
║ Neuromorphic Assistant Ready!        ║
╚═══════════════════════════════════════╝
Time: 08:30
```

### **2. Home Screen Appears**
```
╔═══════════════════════════════════════╗
║  [Calendar]    [AI Suggester]       ║
║  [Memory]      [Settings]           ║
╚═══════════════════════════════════════╝
```

**Navigation:**
- Arrow keys to move
- Enter to select
- Q to go back

### **3. Wait for First Notification (~2 minutes)**

OS time advances from 08:30 → 08:50

### **4. Notification Appears**
```
╔══════════════════════════════════════╗
║ [!] PROACTIVE SUGGESTION            ║
║ Upcoming: Team Meeting               ║
║ Suggestion: Deep work               ║ ← From YOUR trained model!
║ [Y] Accept  [N] Dismiss             ║
╚══════════════════════════════════════╝
```

### **5. Make Your Choice**

**Press Y (Accept):**
```
✓ Suggestion accepted!
✓ Learning from your choice...  ← SNN learning!
✓ Added to calendar!
```

**OR Press N (Reject):**
```
✗ Suggestion dismissed
✓ Learning from feedback...
```

### **6. Repeat 20-30 Times**

**Continue interacting:**
- Navigate to different apps
- Accept/reject suggestions
- Let OS learn your preferences
- Each choice is logged!

**While you interact:**
- **Terminal 3**: Shows "✓ Collected metrics: X samples"
- **HWiNFO64**: Logs GPU metrics every 1 second
- **QEMU**: OS runs and learns

---

## ⏹️ Stop Collection (After 20-30 Interactions)

### **Step 7: Stop OS Metrics Collector**

**In Terminal 3:**
```
Press Ctrl+C

Output:
Stopping collection...
✓ Metrics saved to: os_runtime_metrics.json
✓ Collected 28 samples
```

### **Step 8: Close QEMU**

**In QEMU window:**
```
Close the window
OR
Press Ctrl+C in Terminal 2
```

### **Step 9: Stop HWiNFO64 Logging**

**Restore HWiNFO64 window:**
```
1. Click on HWiNFO64 in taskbar
2. In Sensors window, click "Logging Stop" button
3. Logging stops
4. File is saved
```

**You can close HWiNFO64 now.**

---

## 📊 Combine the Data

### **Step 10: Navigate to Neuromorphic Assistant**

**In Terminal 3 (or any terminal):**
```bash
cd C:\path\to\minios\neuromorphic_assistant
```

### **Step 11: Run Combination Script**

**Windows PowerShell:**
```powershell
python combine_hwinfo_metrics.py `
    --hwinfo C:\hwinfo_logs\session_1.csv `
    --os os_runtime_metrics.json `
    --output combined_metrics.json `
    --graph combined_metrics_graph.png
```

**Windows Command Prompt:**
```cmd
python combine_hwinfo_metrics.py ^
    --hwinfo C:\hwinfo_logs\session_1.csv ^
    --os os_runtime_metrics.json ^
    --output combined_metrics.json ^
    --graph combined_metrics_graph.png
```

### **Step 12: Wait for Processing**

**Expected output:**
```
📊 Combining HWiNFO64 + MiniOS Metrics
============================================================
Loading HWiNFO64 data from: C:\hwinfo_logs\session_1.csv
  Found 623 samples
  ✓ Found GPU power: GPU PPT
  ✓ Found GPU temp: GPU Temperature
  ✓ Found GPU memory: GPU D3D Memory Dedicated
  ✓ Parsed timestamps

Loading OS metrics from: os_runtime_metrics.json
  ✓ Found 28 OS samples

Correlating metrics (window: ±2.0s)...
  ✓ Matched 27/28 OS samples with HWiNFO64 data

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
  Final Accuracy: 75.2%
  Total Samples: 27

Energy Consumption:
  Session duration: 10.5 minutes
  Total energy: 20.67 Wh

============================================================

✓ Visualization saved to: combined_metrics_graph.png

✓ Complete!

Files created:
  - combined_metrics.json (combined data)
  - combined_metrics_graph.png (visualization)
```

---

## 🎉 View Your Results!

### **Step 13: Open the Graph**

```
Open: combined_metrics_graph.png

You'll see 4 panels:
  ┌─────────────────┬─────────────────┐
  │ OS Accuracy     │ Inference Time  │
  │ (Learning!)     │ (Latency)       │
  ├─────────────────┼─────────────────┤
  │ GPU Power       │ GPU Temperature │
  │ (Real HWiNFO64) │ (Real HWiNFO64) │
  └─────────────────┴─────────────────┘
```

### **Step 14: Check the JSON Data**

**Open: combined_metrics.json**

```json
{
  "data": [
    {
      "timestamp": "2025-03-15T...",
      
      // YOUR 8 REQUIRED METRICS:
      "accuracy": 75.2,                    // #1 ✅
      "ram_mb": 1024.5,                    // #2 ✅
      "gpu_allocated_mb": 542.3,           // #3 ✅ (HWiNFO64)
      "gpu_reserved_mb": 4096.0,           // #4 ✅ (HWiNFO64)
      "gpu_power_watts_actual": 121.3,     // #5 ✅ (HWiNFO64)
      "energy_wh": 0.0234,                 // #6 ✅ (Calculated)
      "time_seconds": 45.2,                // #7 ✅
      "avg_inference_ms": 12.4,            // #8 ✅
      
      // Bonus metrics:
      "gpu_temp_c_actual": 67.2,
      "total_inferences": 5,
      "total_accepts": 3,
      "total_rejects": 2
    }
  ]
}
```

---

## ✅ Success Checklist

After completing all steps:

- [ ] HWiNFO64 CSV exists (C:\hwinfo_logs\session_1.csv)
- [ ] OS metrics JSON exists (os_runtime_metrics.json)
- [ ] Combination script ran successfully
- [ ] combined_metrics.json created
- [ ] combined_metrics_graph.png created
- [ ] All 8 metrics present in JSON
- [ ] Graph shows 4 panels with data

**All checked?** ✅ SUCCESS! You have complete metrics!

---

## 📁 Files You'll Have

```
C:\hwinfo_logs\
└── session_1.csv                       ← HWiNFO64 GPU data

minios\
├── os_metrics.log                      ← QEMU serial output
└── neuromorphic_assistant\
    ├── os_runtime_metrics.json         ← OS interaction data
    ├── combined_metrics.json           ← ALL 8 METRICS! ✅
    └── combined_metrics_graph.png      ← Visualization
```

---

## 🎯 Quick Command Reference

```bash
# === PHASE 1: Start Everything ===

# Terminal 1: HWiNFO64
Click "Logging Start" → Save to session_1.csv → Minimize

# Terminal 2: Run OS
cd minios
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -serial file:os_metrics.log

# Terminal 3: Collect OS metrics
cd minios\neuromorphic_assistant
python collect_os_metrics.py --mode collect --source file --logfile ..\os_metrics.log

# === PHASE 2: Interact ===
# Use OS for 10 minutes, 20-30 interactions

# === PHASE 3: Stop ===
# Terminal 3: Ctrl+C
# Terminal 2: Close QEMU
# HWiNFO64: Click "Logging Stop"

# === PHASE 4: Combine ===
cd minios\neuromorphic_assistant
python combine_hwinfo_metrics.py --hwinfo C:\hwinfo_logs\session_1.csv --os os_runtime_metrics.json

# === DONE! ===
# Open combined_metrics_graph.png
# View combined_metrics.json
```

---

## 💡 Tips for Good Data

**For best results:**

1. **Vary your choices** - Mix accepts and rejects
2. **Interact consistently** - Don't rush
3. **Let OS learn** - Notice accuracy improving
4. **Monitor all terminals** - Make sure all are collecting
5. **Run for 10+ minutes** - More data = better insights

---

## 🐛 Troubleshooting

### OS collector shows 0 samples

**Check:**
```bash
type os_metrics.log
# Should show "METRICS_START" blocks
```

**Fix:** Make sure QEMU is running with `-serial file:os_metrics.log`

---

### Combination script fails

**Check:**
```bash
dir C:\hwinfo_logs\session_1.csv
dir os_runtime_metrics.json
# Both files should exist
```

**Fix:** Verify both files were created

---

### No metrics matched

**Increase time window:**
```bash
python combine_hwinfo_metrics.py --hwinfo session_1.csv --os os_runtime_metrics.json --window 5.0
```

---

## 🚀 You're Ready!

**Next steps:**

1. ✅ Click "OK" in HWiNFO64 settings
2. ✅ Click "Logging Start"
3. ✅ Minimize HWiNFO64
4. ✅ Run QEMU (Terminal 2)
5. ✅ Run collector (Terminal 3)
6. ✅ Interact with OS
7. ✅ Stop everything
8. ✅ Combine data
9. ✅ Analyze results!

**Good luck! You'll have complete AMD GPU metrics in about 20 minutes!** 🎉📊
