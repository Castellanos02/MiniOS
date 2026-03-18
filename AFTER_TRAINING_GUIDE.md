# After Training: Complete Workflow to Run OS

## 🎯 You Just Finished Training!

You ran `python train_with_directml.py` and got:

```
Training complete in 78.5s!
✓ Metrics saved to: training_metrics.json
✓ Model saved to: minios_activity_model.npz

✓ Training complete!
  - Model: minios_activity_model.npz
  - Metrics: training_metrics.json

Next step: python export_to_minios.py
```

**What now?** Follow these exact steps:

---

## 📋 Complete Post-Training Workflow

### Step 1: Verify Training Output Files

```bash
# Check that training created the model
ls -lh minios_activity_model.npz

# Should show:
# minios_activity_model.npz  (~50-100 KB)
```

**If file exists:** ✅ Continue to Step 2  
**If file missing:** ❌ Re-run training

---

### Step 2: Export Model to C

**Still in the `neuromorphic_assistant/` folder:**

```bash
python export_to_minios.py
```

**Expected output:**
```
🔧 Exporting neuromorphic_assistant to C for MiniOS

============================================================
Loading model from: minios_activity_model.npz

Exporting model to C...
  Input size: 28
  Hidden size: 32
  Output size: 20
  Timesteps: 30
  Total weights: 1280

✓ Exported to: ../kernel/neuromorphic_assistant_weights.h
  Size: 15.23 KB

✓ Exported context mapping to: ../kernel/neuromorphic_assistant_context.h

============================================================
✓ Export complete!

Next steps:
  1. cd ..
  2. make clean
  3. make iso-carplay
  4. make run-carplay
```

---

### Step 3: Verify Export Created Header Files

```bash
# Check that export created the files
ls -lh ../kernel/neuromorphic_assistant_weights.h
ls -lh ../kernel/neuromorphic_assistant_context.h

# Should show:
# neuromorphic_assistant_weights.h (~15 KB)
# neuromorphic_assistant_context.h (~2 KB)
```

**If files exist:** ✅ Continue to Step 4  
**If files missing:** ❌ Re-run export

---

### Step 4: Go Back to MiniOS Root

```bash
cd ..
pwd
# Should show: .../minios
```

---

### Step 5: Clean Previous Builds

```bash
make clean
```

**Expected output:**
```
Cleaning build directory...
rm -rf build/*
✓ Clean complete
```

---

### Step 6: Build OS with Your Trained Model

```bash
make iso-carplay
```

**Expected output:**
```
Building CarPlay-style kernel with SNN...
====================================================

Compiling multiboot header...
nasm -f elf32 kernel/multiboot_header.asm -o build/multiboot_header.o
✓ Multiboot header compiled

Compiling kernel with neuromorphic assistant...
gcc -m32 -ffreestanding -nostdlib -c kernel/kernel_carplay.c -o build/kernel_carplay.o
  → Including neuromorphic_assistant_weights.h
  → Including neuromorphic_assistant_context.h
  → Including neuromorphic_assistant_learning.c
✓ Kernel compiled

Linking kernel...
ld -m elf_i386 -T kernel/linker_multiboot.ld -o build/kernel_carplay.bin \
   build/multiboot_header.o build/kernel_carplay.o
✓ Kernel linked

Creating ISO with GRUB...
mkdir -p isofiles/boot/grub
cp build/kernel_carplay.bin isofiles/boot/
cp grub.cfg isofiles/boot/grub/
grub-mkrescue -o build/minios_carplay.iso isofiles
✓ ISO created: build/minios_carplay.iso

====================================================
✓ Build complete!

ISO file: build/minios_carplay.iso (5.8 MB)

Run with: make run-carplay
```

---

### Step 7: Verify ISO Was Created

```bash
ls -lh build/minios_carplay.iso

# Should show:
# build/minios_carplay.iso (5-6 MB)
```

**If ISO exists:** ✅ Continue to Step 8  
**If ISO missing or errors:** See troubleshooting below

---

### Step 8: Run Your OS!

```bash
make run-carplay
```

**OR manually:**
```bash
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -boot d
```

**QEMU window opens!**

---

### Step 9: Test Your Trained SNN

**What you should see:**

**1. Boot screen:**
```
╔═══════════════════════════════════════╗
║ MiniOS CarPlay - Neuromorphic SNN    ║
╠═══════════════════════════════════════╣
║ Lava SNN Ready!                      ║
║ Model: 28 -> 32 -> 20 neurons       ║
╚═══════════════════════════════════════╝

Time: 08:30
```

**2. Home screen:**
```
╔═══════════════════════════════════════╗
║  [Calendar]    [AI Suggester]       ║
║  [Memory]      [Settings]           ║
╚═══════════════════════════════════════╝
```

**3. Wait for notification (08:50):**
```
╔══════════════════════════════════════╗
║ [!] PROACTIVE SUGGESTION            ║
║ Upcoming: Team Meeting               ║
║ Suggestion: Deep work               ║  ← From YOUR trained model!
║ [Y] Accept  [N] Dismiss             ║
╚══════════════════════════════════════╝
```

**4. Press Y or N:**
```
✓ Suggestion accepted!
✓ Learning from your choice...  ← YOUR SNN learning!
✓ Added to calendar!
```

---

## 🎮 Using Your OS

### Navigation

**Home Screen:**
- Arrow Keys / WASD / IJKL → Navigate
- Enter / Space → Open app
- Q → Quit

**Calendar:**
- Up/Down → Scroll
- B/Q → Back

**Notifications:**
- Y → Accept (SNN learns!)
- N → Reject (SNN learns!)

---

## ✅ Verification Checklist

After running, verify:

- [ ] OS boots successfully
- [ ] Home screen shows 4 apps
- [ ] Time updates (08:30 → 08:31 → ...)
- [ ] Notification appears at 08:50
- [ ] Suggestion shown (from your model!)
- [ ] Can press Y or N
- [ ] "Learning from your choice..." appears
- [ ] Suggestion adds to calendar when accepted

**If all checked:** ✅ SUCCESS! Your SNN is working!

---

## 🔄 Complete Command Summary

```bash
# === After training completes ===

# 1. Export model to C
python export_to_minios.py

# 2. Go back to root
cd ..

# 3. Clean and build
make clean
make iso-carplay

# 4. Run!
make run-carplay

# === Done! ===
```

**Time:** ~2-3 minutes total

---

## 📊 Optional: Visualize Training Metrics

**Before or after running OS:**

```bash
cd neuromorphic_assistant

# Create training graphs
python visualize_metrics.py
```

**Output:**
- `snn_training_metrics.png` - Beautiful 9-panel graph
- Shows accuracy, loss, power, energy, etc.

---

## 🔬 Optional: Collect Runtime Metrics

**If you want to track metrics while OS runs:**

**Terminal 1:**
```bash
qemu-system-x86_64 -cdrom build/minios_carplay.iso \
    -m 256M -serial file:os_metrics.log
```

**Terminal 2:**
```bash
cd neuromorphic_assistant
python collect_os_metrics.py --mode collect --source file
```

**After interaction:**
```bash
python collect_os_metrics.py --mode visualize
```

**Output:**
- `os_runtime_metrics.json` - All interaction data
- `os_runtime_graphs.png` - Runtime visualization

---

## 🐛 Troubleshooting

### Issue: "neuromorphic_assistant_weights.h: No such file"

**Problem:** Export didn't create header files

**Solution:**
```bash
cd neuromorphic_assistant
python export_to_minios.py
cd ..
make clean
make iso-carplay
```

---

### Issue: "minios_activity_model.npz not found"

**Problem:** Training didn't save model

**Solution:**
```bash
cd neuromorphic_assistant

# Check if file exists
ls minios_activity_model.npz

# If missing, re-train
python train_with_directml.py
# OR use fast version
python train_minios_model_FAST.py
```

---

### Issue: Build fails with "gcc: command not found"

**Problem:** Build tools not installed

**Solution:**
```bash
# Ubuntu/WSL
sudo apt install build-essential nasm make

# Then retry
make clean
make iso-carplay
```

---

### Issue: "grub-mkrescue: command not found"

**Problem:** GRUB tools not installed

**Solution:**
```bash
sudo apt install grub-pc-bin grub-common xorriso

# Then retry
make clean
make iso-carplay
```

---

### Issue: QEMU doesn't start

**Problem:** QEMU not installed

**Solution:**
```bash
sudo apt install qemu-system-x86

# Then retry
make run-carplay
```

---

### Issue: Notification doesn't appear

**Problem:** Need to wait for OS time to reach 08:50

**Solution:**
- OS starts at 08:30
- Time advances in real-time (accelerated)
- Wait ~2 minutes real time
- Notification appears at 08:50 OS time

---

### Issue: "Learning from your choice" doesn't show

**Problem:** Learning code not integrated in kernel

**Solution:**
Check `kernel/kernel_carplay.c` has:
```c
#include "neuromorphic_assistant_learning.c"
```

If missing, see `INTEGRATION_INSTRUCTIONS.md`

---

## 📁 File Locations After Export

```
minios/
├── neuromorphic_assistant/
│   ├── minios_activity_model.npz       ← Trained model
│   ├── training_metrics.json           ← Training data
│   ├── export_to_minios.py             ← Export script
│   └── ...
├── kernel/
│   ├── neuromorphic_assistant_weights.h    ← Generated (15 KB)
│   ├── neuromorphic_assistant_context.h    ← Generated (2 KB)
│   ├── neuromorphic_assistant_learning.c   ← Learning code
│   └── kernel_carplay.c                    ← Main kernel
└── build/
    └── minios_carplay.iso              ← Bootable OS (6 MB)
```

---

## 🎯 Quick Reference

**After training:**
1. ✅ `python export_to_minios.py`
2. ✅ `cd ..`
3. ✅ `make clean && make iso-carplay`
4. ✅ `make run-carplay`
5. ✅ Test your SNN!

**Total time:** 2-3 minutes

---

## 🎓 What Your Model Is Doing

**Your trained SNN:**
- Has learned 20 activity patterns
- Input: Time, energy, engagement
- Hidden: 32 neurons
- Output: 20 activity suggestions
- Trained for: 15 epochs
- Accuracy: ~75-88%

**In the OS:**
- Suggests activities based on context
- Learns from your feedback (Y/N)
- Updates weights in real-time
- Gets better with each interaction

---

## 🎉 Success!

**You now have:**
- ✅ Trained Lava SNN model
- ✅ Model exported to C
- ✅ Bootable OS with SNN
- ✅ Real-time learning from feedback
- ✅ Training metrics/graphs

**Your neuromorphic OS is running!** 🧠⚡

---

## 🚀 Next Steps (Optional)

### Compare Models

Train with different settings:
```bash
# Train larger model
# Edit train_with_directml.py: hidden_size=64
python train_with_directml.py
python export_to_minios.py
make clean && make iso-carplay && make run-carplay
```

### Test Different Activities

Modify `ACTIVITY_CLASSES` in training script, retrain, test.

### Collect Research Data

Use HWiNFO64 + OS collector for publication-quality metrics.

### Compare GPUs

Run on NVIDIA, compare with AMD results.

---

**You're all set! Just run those 4 commands and test your SNN!** 🎯
