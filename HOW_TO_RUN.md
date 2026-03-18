# Complete Steps to Run Neuromorphic MiniOS

## 🎯 Quick Overview

You have 3 options:
1. **Quick Test** - Run basic OS without SNN (5 minutes)
2. **CPU-based SNN** - Run with trained model, no GPU (30 minutes)
3. **GPU-accelerated with Metrics** - Full system with monitoring (1 hour)

---

## ⚡ Option 1: Quick Test (Fastest - No SNN Training)

**Just want to see the OS work?**

```bash
# 1. Extract archive
cd ~
tar -xzf minios.tar.gz
cd minios

# 2. Build
make clean
make iso-carplay

# 3. Run
make run-carplay
```

**What you get:**
- ✅ CarPlay interface
- ✅ Proactive notifications
- ✅ Calendar
- ✅ Simple rule-based suggestions (not SNN)
- ⏱️ Time: 5 minutes

**Skip to this if you just want to test the OS interface!**

---

## 🧠 Option 2: CPU-based SNN (Recommended for Testing)

**Want the SNN but don't need GPU metrics?**

### Step 1: Install Dependencies

```bash
pip install numpy lava-nc
```

### Step 2: Navigate and Train

```bash
cd ~/minios/neuromorphic_assistant

# Use FAST training (2-5 minutes)
python train_minios_model_FAST.py
```

**Expected output:**
```
🚀 MiniOS Neuromorphic Assistant - FAST Training

⚡ OPTIMIZED FOR SPEED:
  - Reduced timesteps: 20 (was 50)
  - Reduced training samples: 50 (was 200)
  - Reduced epochs: 10 (was 30)

Training for 10 epochs...
Epoch  1/10: Loss = 0.4123, Accuracy = 40.0%, Time = 3.2s
Epoch  5/10: Loss = 0.2134, Accuracy = 68.0%, Time = 3.0s
Epoch 10/10: Loss = 0.1234, Accuracy = 78.0%, Time = 2.9s

Training complete in 31.2s!
✓ Model saved to: minios_activity_model.npz
```

### Step 3: Export to C

```bash
# Still in neuromorphic_assistant folder
python export_to_minios.py
```

**Expected output:**
```
Exporting model to C...
✓ Exported to: ../kernel/neuromorphic_assistant_weights.h
✓ Exported context mapping to: ../kernel/neuromorphic_assistant_context.h
```

### Step 4: Build OS

```bash
cd ..  # Back to minios/
make clean
make iso-carplay
```

**Expected output:**
```
Building CarPlay-style kernel...
gcc ... kernel_carplay.c ...
✓ Built CarPlay kernel
✓ Created: build/minios_carplay.iso
```

### Step 5: Run!

```bash
make run-carplay
```

**What you get:**
- ✅ Full neuromorphic SNN
- ✅ Real-time learning from feedback
- ✅ Activity suggestions
- ✅ Works on any machine
- ⏱️ Time: 30 minutes total

---

## 🚀 Option 3: GPU-Accelerated with Full Metrics (Research Mode)

**Want GPU metrics and graphs for research?**

### Step 1: Install All Dependencies

```bash
# For NVIDIA RTX 4060
pip install nvidia-ml-py3 numpy lava-nc psutil matplotlib

# OR for AMD RX 5500 XT
pip install amdsmi numpy lava-nc psutil matplotlib
```

### Step 2: Train with GPU Monitoring

```bash
cd ~/minios/neuromorphic_assistant

# Train with comprehensive metrics collection
python train_with_gpu_metrics.py
```

**Expected output:**
```
GPU-ACCELERATED SNN TRAINING WITH METRICS COLLECTION
✓ Detected NVIDIA GPU: NVIDIA GeForce RTX 4060

Training with GPU monitoring...
----------------------------------------------------------------------
Epoch  Loss       Acc%     Time(s)  Power(W)   Energy(Wh)   RAM(MB)    GPU(MB)
----------------------------------------------------------------------
1      0.4523     42.0     4.2      85.3       0.0100       1024.5     512.3
5      0.2134     75.0     21.3     86.5       0.0502       1035.1     518.4
10     0.1456     84.0     42.7     85.8       0.1004       1042.3     519.8
15     0.1123     88.0     63.5     85.5       0.1502       1045.2     520.1

Training Summary:
  Total time: 63.5 seconds
  Total energy: 0.1502 Wh
  Final accuracy: 88.0%
  
✓ Metrics saved to: training_metrics.json
✓ Model saved to: minios_activity_model.npz
```

### Step 3: Create Training Graphs

```bash
python visualize_metrics.py
```

**Output:**
- `snn_training_metrics.png` - Beautiful 9-panel graph

### Step 4: Export Model

```bash
python export_to_minios.py
```

### Step 5: Configure GPU in Kernel

**Edit `kernel/neuromorphic_assistant_gpu.c`:**

```c
// For NVIDIA RTX 4060:
#define USE_GPU 1
#define GPU_TYPE_NVIDIA 1

// For AMD RX 5500 XT:
#define USE_GPU 1
#define GPU_TYPE_NVIDIA 0
```

### Step 6: Update Kernel Integration

**Edit `kernel/kernel_carplay.c` to use GPU version:**

Find this line:
```c
#include "neuromorphic_assistant_learning.c"
```

Change to:
```c
#include "neuromorphic_assistant_gpu.c"
```

And update initialization:
```c
// In kernel_main():
na_metrics_init();
```

### Step 7: Build OS

```bash
cd ..
make clean
make iso-carplay
```

### Step 8: Run with Metrics Collection

**Terminal 1 - Run OS:**
```bash
qemu-system-x86_64 -cdrom build/minios_carplay.iso \
    -m 256M -serial file:os_metrics.log
```

**Terminal 2 - Collect Metrics:**
```bash
cd neuromorphic_assistant
python collect_os_metrics.py --mode collect \
    --source file --logfile ../os_metrics.log
```

**Interact with the OS, then press Ctrl+C in Terminal 2**

### Step 9: Create Runtime Graphs

```bash
python collect_os_metrics.py --mode visualize
```

**Output:**
- `os_runtime_graphs.png` - Real user interaction data!

**What you get:**
- ✅ GPU-accelerated inference
- ✅ Complete training metrics
- ✅ Runtime metrics from OS
- ✅ Publication-ready graphs
- ⏱️ Time: 1 hour total

---

## 📋 Minimal Quick Start (Recommended)

**If you just want to run it NOW:**

```bash
# 1. Extract
tar -xzf minios.tar.gz && cd minios

# 2. Install basics
pip install numpy lava-nc

# 3. Train (fast version)
cd neuromorphic_assistant
python train_minios_model_FAST.py

# 4. Export
python export_to_minios.py

# 5. Build
cd ..
make clean && make iso-carplay

# 6. Run!
make run-carplay
```

**Done! Your neuromorphic OS is running!** 🎉

---

## 🎮 Using the OS

### Navigation

**Home Screen:**
- Arrow Keys / WASD / IJKL - Navigate between apps
- Enter / Space - Open selected app
- Q - Quit

**Calendar:**
- Up/Down - Scroll events
- A - Add suggestion
- B/Q - Back to home

**Notifications:**
- Y - Accept suggestion (OS learns!)
- N - Reject suggestion (OS learns!)

### Expected Behavior

**Boot:**
```
╔═══════════════════════════════════════╗
║ MiniOS CarPlay                       ║
╠═══════════════════════════════════════╣
║  [Calendar]    [AI Suggester]       ║
║  [Memory]      [Settings]           ║
╚═══════════════════════════════════════╝
Time: 08:30
```

**First Notification (08:50):**
```
╔══════════════════════════════════════╗
║ [!] PROACTIVE SUGGESTION            ║
║ Upcoming: Team Meeting               ║
║ Suggestion: Silence phone           ║
║ [Y] Accept  [N] Dismiss             ║
║ Time left: 04:57                    ║
╚══════════════════════════════════════╝
```

**Press Y:**
```
✓ Suggestion accepted!
✓ Learning from your choice...  ← SNN learning!
✓ Added to calendar!
```

---

## 🔍 Verification Checklist

**After running, verify:**

- [ ] OS boots successfully
- [ ] Home screen displays 4 apps
- [ ] Time shows in top-right
- [ ] Can navigate with arrows
- [ ] Calendar opens and shows events
- [ ] Notification appears at 08:50
- [ ] Can accept/reject suggestions
- [ ] "Learning from your choice..." appears
- [ ] Suggestions add to calendar

---

## ⚙️ Troubleshooting

### Training Errors

**Error: `ModuleNotFoundError: No module named 'lava'`**

```bash
pip install lava-nc numpy
```

**Error: `ImportError: attempted relative import`**

✅ Already fixed! Just make sure you're in the `neuromorphic_assistant/` folder:
```bash
cd minios/neuromorphic_assistant
python train_minios_model_FAST.py
```

**Training too slow (>5 min/epoch)?**

Use the FAST version:
```bash
python train_minios_model_FAST.py  # Not train_minios_model.py
```

---

### Build Errors

**Error: `neuromorphic_assistant_weights.h: No such file`**

You forgot to export the model:
```bash
cd neuromorphic_assistant
python export_to_minios.py
cd ..
make clean && make iso-carplay
```

**Error: `gcc: command not found`**

```bash
sudo apt install build-essential nasm make
```

**Error: `grub-mkrescue: command not found`**

```bash
sudo apt install grub-pc-bin grub-common xorriso
```

---

### QEMU Errors

**Error: `qemu-system-x86_64: command not found`**

```bash
sudo apt install qemu-system-x86
```

**QEMU window doesn't open (WSL)?**

Use MSYS2 on Windows:
```bash
# In WSL - build
make iso-carplay

# Copy to Windows
cp build/minios_carplay.iso /mnt/c/Users/YOUR_USERNAME/Downloads/

# In MSYS2 - run
cd /c/Users/YOUR_USERNAME/Downloads
qemu-system-x86_64 -cdrom minios_carplay.iso -m 256M
```

---

## 📊 File Locations

**After setup, you'll have:**

```
minios/
├── Makefile
├── kernel/
│   ├── kernel_carplay.c              # Main OS code
│   ├── neuromorphic_assistant_weights.h    # Generated weights
│   ├── neuromorphic_assistant_context.h    # Generated context
│   ├── neuromorphic_assistant_learning.c   # Learning code
│   └── neuromorphic_assistant_gpu.c        # GPU version
├── neuromorphic_assistant/
│   ├── *.py                          # Your Lava code
│   ├── train_minios_model.py         # Full training
│   ├── train_minios_model_FAST.py    # Fast training ⚡
│   ├── export_to_minios.py           # Export to C
│   ├── train_with_gpu_metrics.py     # GPU monitoring
│   ├── collect_os_metrics.py         # Runtime metrics
│   └── visualize_metrics.py          # Create graphs
└── build/
    └── minios_carplay.iso            # Bootable OS (created by make)
```

---

## 🎯 Recommended Path for First Time

```bash
# === FAST PATH (30 minutes) ===

# 1. Extract
tar -xzf minios.tar.gz && cd minios

# 2. Install
pip install numpy lava-nc

# 3. Navigate
cd neuromorphic_assistant

# 4. Train (FAST)
python train_minios_model_FAST.py
# Wait 2-5 minutes

# 5. Export
python export_to_minios.py

# 6. Build
cd ..
make clean
make iso-carplay

# 7. Run
make run-carplay

# 8. Test!
# - Wait for notification at 08:50
# - Press Y or N
# - See "Learning from your choice..."
# - Success! 🎉
```

---

## 💡 Pro Tips

**Speed up testing:**
- Use `train_minios_model_FAST.py` (not regular version)
- Reduces training from 20 min to 2-5 min
- Still produces working model!

**If training is interrupted:**
- Ctrl+C to stop
- Delete `minios_activity_model.npz` if corrupted
- Run training again

**Multiple tests:**
```bash
# Quick rebuild
make clean && make iso-carplay && make run-carplay
```

**Check if ISO was created:**
```bash
ls -lh build/minios_carplay.iso
# Should show ~6MB file
```

---

## ✅ Success Indicators

**You'll know it's working when:**

1. ✅ Training completes with accuracy ~75-85%
2. ✅ Export creates `.h` files in `kernel/`
3. ✅ Build completes without errors
4. ✅ ISO file created (~6 MB)
5. ✅ QEMU opens with OS
6. ✅ Home screen shows 4 apps
7. ✅ Time advances (08:30, 08:31, ...)
8. ✅ Notification appears at 08:50
9. ✅ "Learning from your choice..." when you press Y
10. ✅ Suggestions add to calendar

---

## 🚀 You're Ready!

**Pick your path:**

- **Just want to see it?** → Option 1 (Quick Test)
- **Want the SNN working?** → Option 2 (CPU-based)
- **Need research data?** → Option 3 (GPU + Metrics)

**Most common choice:** Option 2 with FAST training! 🎯

Good luck! Let me know if you hit any issues! 🚀
