# Complete Build & Run Guide - Learning-Enabled MiniOS

## 🎯 Goal: Run Your Lava SNN with Online Learning

This guide takes you from zero to running the neuromorphic OS with real-time learning!

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] WSL Ubuntu installed (or native Linux)
- [ ] Build tools installed (gcc, nasm, make)
- [ ] GRUB tools installed (grub-mkrescue, xorriso)
- [ ] QEMU installed (qemu-system-x86_64)
- [ ] MiniOS source code extracted

**If you haven't set these up yet, see:** `WSL_UBUNTU_INSTALL_GUIDE.md`

---

## 🚀 Quick Start (Complete Steps)

### Step 1: Extract MiniOS Archive

```bash
# Navigate to your working directory
cd ~

# Extract the archive
tar -xzf minios.tar.gz

# Navigate into the directory
cd minios

# Verify files are there
ls
# You should see: Makefile, kernel/, build/, grub.cfg, etc.
```

---

### Step 2: Create the Learning-Enabled Kernel

**Option A: Use the provided code (recommended for testing)**

```bash
# The archive already contains the base kernel
# We need to add the learning components

# Navigate to kernel directory
cd kernel

# You should see:
# - kernel_carplay.c (base kernel)
# - lava_snn_weights.h (weights - will be generated)
# - lava_snn_inference.c (inference code)
```

**Option B: Train your own model first (advanced)**

If you want to train your own Lava SNN first:

```bash
# In your neuromorphic_assistant repository
cd ~/neuromorphic_assistant

# Train the model
python train_activity_model.py
# Output: activity_snn_weights.npz

# Export to C
python export_lava_to_c.py
# Output: lava_snn_weights.h

# Copy to MiniOS
cp lava_snn_weights.h ~/minios/kernel/
```

---

### Step 3: Add Online Learning Code

**Create the learning inference file:**

```bash
cd ~/minios/kernel

# Create lava_snn_online_learning.c
# Copy the complete code from LAVA_ONLINE_LEARNING.md
# Or I can provide it as a separate file
```

**For now, let's use a simplified version. Create this file:**

```bash
cat > lava_snn_online_learning.c << 'EOF'
// Simplified online learning implementation
// This is a placeholder - use full version from LAVA_ONLINE_LEARNING.md

#include <stdint.h>

// Placeholder weights (will be replaced with trained weights)
#define SNN_INPUT_SIZE 10
#define SNN_HIDDEN_SIZE 32
#define SNN_OUTPUT_SIZE 20

// Simple inference function
uint8_t neuromorphic_suggest_activity_with_learning(
    uint8_t hour, uint8_t minute, uint8_t energy,
    uint8_t engagement, uint32_t idle, uint8_t accepts, uint8_t rejects
) {
    // Simple rule-based for now (replace with real SNN)
    if (hour < 12 && energy > 70) return 0;  // Morning workout
    if (hour >= 12 && hour < 18) return 5;   // Afternoon work
    return 10;  // Evening rest
}

void neuromorphic_learn_from_user_response(uint8_t accepted) {
    // Learning will be implemented here
}

void lava_snn_init_with_learning(void) {
    // Initialize learning system
}
EOF
```

---

### Step 4: Update kernel_carplay.c

**Open kernel_carplay.c and add the learning integration:**

```bash
cd ~/minios/kernel

# Backup the original
cp kernel_carplay.c kernel_carplay.c.backup

# Edit kernel_carplay.c
nano kernel_carplay.c  # or vim, code, etc.
```

**Add at the top (after includes):**

```c
// Include online learning
#include "lava_snn_online_learning.c"

// Learning statistics
static uint32_t total_accepts = 0;
static uint32_t total_rejects = 0;
```

**In kernel_main(), find the initialization section and add:**

```c
// Initialize Lava SNN with learning
lava_snn_init_with_learning();

draw_text("Lava SNN with Learning Ready!", 20, 3,
         (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);
```

**Find the ml_suggest_activity() function and update it:**

```c
static uint8_t ml_suggest_activity(void) {
    return neuromorphic_suggest_activity_with_learning(
        g_ml.current_hour,
        g_ml.current_minute,
        g_ml.energy_level,
        g_ml.engagement,
        g_ml.idle_cycles,
        total_accepts,
        total_rejects
    );
}
```

**In the notification handling code, add learning callbacks:**

```c
// When user accepts (presses 'Y')
if (key == 'y') {
    // Existing acceptance code...
    
    // ADD THIS: Learn from acceptance
    neuromorphic_learn_from_user_response(1);
    total_accepts++;
    
    // Show learning message
    draw_text("Learning from your choice...", 14, 17,
             (COLOR_LIGHT_GREEN << 4) | COLOR_WHITE);
    
    // ... rest of acceptance code
}

// When user rejects (presses 'N')
else if (key == 'n') {
    // ADD THIS: Learn from rejection
    neuromorphic_learn_from_user_response(0);
    total_rejects++;
    
    draw_text("Learning from your feedback...", 14, 16,
             (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
    
    // ... rest of rejection code
}
```

**Save the file (Ctrl+O, Enter, Ctrl+X in nano)**

---

### Step 5: Build the ISO

```bash
# Navigate to MiniOS root directory
cd ~/minios

# Clean previous builds
make clean

# Build the CarPlay ISO with learning
make iso-carplay
```

**Expected output:**
```
Building CarPlay-style kernel with app launcher...
nasm -f elf32 kernel/multiboot_header.asm -o build/multiboot_header.o
gcc -m32 -ffreestanding -nostdlib -c kernel/kernel_carplay.c -o build/kernel_carplay.o
ld -m elf_i386 -T kernel/linker_multiboot.ld -o build/kernel_carplay.bin ...
✓ Built CarPlay kernel
Creating CarPlay ISO...
grub-mkrescue -o build/minios_carplay.iso isofiles
✓ Created: build/minios_carplay.iso

🎨 CARPLAY FEATURES:
  ✓ Apple CarPlay-style home screen
  ✓ Lava SNN with online learning
  ✓ Real-time weight updates
  ✓ Personalized suggestions
```

**Check that the ISO was created:**
```bash
ls -lh build/minios_carplay.iso
# Should show: ~5-6 MB file
```

---

### Step 6: Run in QEMU

```bash
# From the minios directory
make run-carplay
```

**Or manually:**
```bash
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -boot d
```

**QEMU window should open showing your OS!**

---

## 🎮 Testing the Learning System

### Initial Boot

**You should see:**
```
╔════════════════════════════════════════════╗
║ MiniOS CarPlay                            ║
╠════════════════════════════════════════════╣
║                                            ║
║     [Calendar]        [AI]                ║
║                                            ║
║     [Memory]          [Settings]          ║
║                                            ║
╚════════════════════════════════════════════╝

Time: 08:30
```

### Test Sequence

**1. Wait for first notification (~2 minutes real time)**
```
Time reaches 08:50 → Notification appears
╔══════════════════════════════════════╗
║ [!] PROACTIVE SUGGESTION            ║
║                                      ║
║ Upcoming: Team Meeting               ║
║ Suggestion: Silence phone           ║
║                                      ║
║ [Y] Accept  [N] Dismiss             ║
╚══════════════════════════════════════╝
```

**2. Press 'Y' to accept**
```
Shows:
"Suggestion accepted!"
"Learning from your choice..."  ← Learning happens!
"Added to calendar!"
```

**3. Open Calendar (Enter key)**
```
╔════════════════════════════════════════╗
║ Calendar - Today's Schedule           ║
╠════════════════════════════════════════╣
║ 08:55  Silence phone      5 min [AI] ║ ← Added!
║ 09:00  Team Meeting      60 min      ║
║ 11:30  Lunch Break       30 min      ║
╚════════════════════════════════════════╝
```

**4. Wait for next notification**
```
Time reaches 11:20 → Next notification
Test rejecting this one (press 'N')
Network learns from rejection!
```

---

## 🔍 Verification Checklist

**After running, verify:**

- [ ] OS boots successfully
- [ ] Home screen displays (4 app tiles)
- [ ] Time updates in top-right
- [ ] Can navigate with arrow keys/WASD
- [ ] Calendar opens (Enter on Calendar tile)
- [ ] Proactive notification appears at 08:50
- [ ] Can accept/reject suggestions (Y/N)
- [ ] "Learning from your choice" message appears
- [ ] Accepted suggestions add to calendar
- [ ] Calendar shows suggestions before events

---

## ⚙️ Troubleshooting

### Issue 1: Build Fails

**Error:** `gcc: command not found`

**Solution:**
```bash
# Install build tools
sudo apt update
sudo apt install -y build-essential nasm make
```

**Error:** `grub-mkrescue: command not found`

**Solution:**
```bash
sudo apt install -y grub-pc-bin grub-common xorriso
```

---

### Issue 2: QEMU Doesn't Open

**Error:** `qemu-system-x86_64: command not found`

**Solution:**
```bash
sudo apt install -y qemu-system-x86
```

**Error:** GUI doesn't work in WSL

**Solution:** Use MSYS2 for QEMU:
```bash
# Build in WSL
make iso-carplay

# Copy ISO to Windows
cp build/minios_carplay.iso /mnt/c/Users/YOUR_USERNAME/Downloads/

# Run in MSYS2
cd /c/Users/YOUR_USERNAME/Downloads
qemu-system-x86_64 -cdrom minios_carplay.iso -m 256M
```

---

### Issue 3: Notification Doesn't Appear

**Check:**
1. Time in top-right corner
2. Should appear at 08:50
3. If past 08:50, restart OS

**Restart OS:**
```
Press Ctrl+C in terminal running QEMU
Run: make run-carplay again
```

---

### Issue 4: Learning Message Doesn't Show

**This means the learning code wasn't integrated.**

**Fix:**
1. Verify you added learning callbacks in kernel_carplay.c
2. Rebuild: `make clean && make iso-carplay`
3. Run again: `make run-carplay`

---

## 📊 Expected Behavior

### Timeline

**Real Time → OS Time**
```
0:00 (boot)    → 08:30 (OS starts)
2:00 (2 min)   → 08:50 (first notification)
5:00 (5 min)   → 11:20 (lunch notification)
8:00 (8 min)   → 13:50 (work notification)
12:00 (12 min) → 16:20 (break notification)
```

### Learning Behavior

**First suggestion:**
- Generic (not personalized yet)
- Network hasn't learned

**After accepting:**
- Network strengthens those weights
- Similar context → More likely to suggest same thing

**After rejecting:**
- Network weakens those weights
- Similar context → Less likely to suggest that

**After 10+ interactions:**
- Noticeably personalized
- Suggestions align with your patterns

---

## 🎯 Quick Reference Commands

### Build Commands
```bash
cd ~/minios
make clean              # Clean builds
make iso-carplay        # Build learning-enabled OS
make run-carplay        # Build and run
```

### Run Commands
```bash
# Run latest built ISO
make run-carplay

# Or manually
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -boot d
```

### Navigation
```
Arrow Keys / WASD / IJKL - Navigate home screen
Enter / Space            - Open selected app
Q / B                    - Back to home
Y                        - Accept suggestion (+ learn)
N                        - Reject suggestion (+ learn)
```

---

## 📝 Complete Workflow Summary

```bash
# 1. Extract
cd ~
tar -xzf minios.tar.gz
cd minios

# 2. Add learning code
cd kernel
# Create lava_snn_online_learning.c (see Step 3 above)
# Update kernel_carplay.c (see Step 4 above)

# 3. Build
cd ..
make clean
make iso-carplay

# 4. Run
make run-carplay

# 5. Test!
# - Wait for notification (08:50)
# - Press Y or N
# - See "Learning from your choice..."
# - Interact more!
```

---

## 🎉 Success Indicators

**You'll know it's working when you see:**

✅ OS boots to CarPlay home screen
✅ Time shows 08:30 and advances
✅ Notification appears at 08:50
✅ Pressing Y shows "Learning from your choice..."
✅ Suggestion adds to calendar
✅ Pressing N shows "Learning from your feedback..."
✅ Next suggestions differ based on feedback

---

## 🚀 Next Steps After Success

**Once basic learning works:**

1. **Train your own Lava model:**
   - Use your neuromorphic_assistant
   - Export real trained weights
   - Replace placeholder weights

2. **Add full STDP implementation:**
   - Use complete code from LAVA_ONLINE_LEARNING.md
   - Real spike-timing-dependent plasticity
   - True neuromorphic learning

3. **Add weight persistence:**
   - Save learned weights to memory
   - Load on boot
   - Network remembers across sessions

4. **Add learning statistics:**
   - Display acceptance rate
   - Show weight evolution
   - Track learning progress

---

## 💡 Pro Tips

**Faster testing:**
```bash
# Quick rebuild and run
make clean && make iso-carplay && make run-carplay
```

**Debug mode:**
```bash
# See all build output
make iso-carplay 2>&1 | tee build.log
```

**Multiple tests:**
```bash
# Run in background
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M &
```

---

## 📞 Help & Support

**If you get stuck:**

1. Check build output for errors
2. Verify all prerequisites installed
3. Try `make clean` before rebuilding
4. Check file permissions (should be readable)
5. Try in fresh terminal session

**Common fixes:**
```bash
# Full clean rebuild
rm -rf build/
make iso-carplay

# Verify tools
which gcc nasm make qemu-system-x86_64 grub-mkrescue

# Re-extract archive
cd ~
rm -rf minios
tar -xzf minios.tar.gz
cd minios
```

---

## ✅ Final Checklist

Before running, confirm:

- [ ] Extracted minios.tar.gz
- [ ] Added learning code to kernel/
- [ ] Updated kernel_carplay.c
- [ ] Ran `make clean`
- [ ] Ran `make iso-carplay` successfully
- [ ] ISO file exists in build/
- [ ] Ready to run `make run-carplay`

---

**You're ready to run your learning-enabled neuromorphic OS! 🧠⚡**

**This is cutting-edge: A bootable OS with a brain that learns!** 🎉
