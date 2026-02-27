# MiniOS Quick Start - FIXED

## The Issue You Encountered

You ran `make clean` which deleted the ISO file, then tried to run it. The correct sequence is:

## Correct Build Sequence

### Option 1: Use the Script (Easiest)

```bash
cd minios
./build_and_run.sh
```

This script does everything automatically:
1. Checks for required tools
2. Cleans old build
3. Builds new ISO
4. Runs QEMU

### Option 2: Manual Steps

```bash
cd minios

# Step 1: Clean (if needed)
make clean

# Step 2: Build ISO
make iso

# Step 3: Run in QEMU
make run-iso
```

**Important:** Always run `make iso` after `make clean`!

## First Time Setup

### Install Required Tools

```bash
sudo apt-get update
sudo apt-get install -y nasm grub-pc-bin xorriso mtools qemu-system-x86
```

### Verify Installation

```bash
which nasm              # Should show /usr/bin/nasm
which grub-mkrescue     # Should show path to grub-mkrescue
which qemu-system-x86_64  # Should show path to qemu
```

## Using the Bootable Version

### Full Build and Run

```bash
cd minios
make clean       # Remove old files
make iso         # Build bootable ISO
make run-iso     # Run in QEMU
```

### Quick Rebuild (after code changes)

```bash
make iso         # Rebuilds without cleaning
make run-iso     # Run
```

## Using the Simulators

If you just want to use MiniOS without building:

```bash
cd minios

# CarPlay-style GUI (recommended)
./minios_gui

# Or text interface
./minios_simulator
```

These work immediately without any building!

## Common Issues

### Issue: "could not read the boot disk"

**Cause:** ISO file doesn't exist or is corrupted

**Solution:**
```bash
make clean
make iso
make run-iso
```

### Issue: "grub-mkrescue: command not found"

**Cause:** GRUB tools not installed

**Solution:**
```bash
sudo apt-get install grub-pc-bin xorriso mtools
```

### Issue: "nasm: command not found"

**Cause:** NASM not installed

**Solution:**
```bash
sudo apt-get install nasm
```

### Issue: Keyboard doesn't work in QEMU

**Cause:** QEMU window doesn't have focus

**Solution:**
1. Click inside the QEMU window
2. Try pressing keys again
3. If still not working, press Ctrl+Alt+G to grab/release keyboard

### Issue: Build takes long time

**Cause:** Normal - building ISO with GRUB takes time

**Solution:** Be patient, it can take 10-30 seconds

## File Locations

After building:

```
minios/
├── build/
│   ├── minios.iso          ← Bootable ISO (created by 'make iso')
│   ├── minios.bin          ← Kernel binary
│   ├── isodir/             ← ISO structure
│   └── *.o                 ← Object files
├── minios_gui              ← GUI simulator (pre-built)
├── minios_simulator        ← Text simulator (pre-built)
└── build_and_run.sh        ← Helper script
```

## Testing Checklist

Before running, verify:

```bash
# 1. Check build directory exists
ls build/

# 2. Check ISO was created
ls -lh build/minios.iso
# Should show file size (e.g., 4.2M)

# 3. Check ISO structure
file build/minios.iso
# Should say: "DOS/MBR boot sector; partition 2 : ID=0xef"

# 4. Run
make run-iso
```

## What to Expect

### GRUB Menu (first screen)

```
GNU GRUB

  MiniOS - Neural Activity Suggester
  MiniOS - Safe Mode

Use ↑ and ↓ to select, Enter to boot
```

Press Enter on first option.

### MiniOS GUI (after GRUB)

```
════════════════════════════════════
  MiniOS - Neural Activity Suggester
════════════════════════════════════

┌──────────────────────────────────┐
│ Suggested Activity:              │
│                                  │
│ Take a 15-minute walk outside    │
│                                  │
│ [A] Accept  [R] Reject  [N] Next │
└──────────────────────────────────┘
```

Now press A, R, or N keys!

## Debugging

### Enable Verbose Output

```bash
# See what make is doing
make iso V=1

# Run QEMU with serial output
qemu-system-x86_64 -cdrom build/minios.iso -serial stdio
```

### Check ISO Contents

```bash
# Mount ISO (Linux)
mkdir -p /tmp/minios_iso
sudo mount -o loop build/minios.iso /tmp/minios_iso
ls -la /tmp/minios_iso/
sudo umount /tmp/minios_iso

# Or use isoinfo
isoinfo -l -i build/minios.iso
```

### Verify Kernel

```bash
# Check kernel file exists in ISO structure
ls -lh build/isodir/boot/minios.bin

# Check it's a valid ELF file
file build/minios.bin
# Should say: "ELF 32-bit LSB executable, Intel 80386"
```

## Quick Reference

### Essential Commands

```bash
# Full build
make clean && make iso && make run-iso

# Quick rebuild
make iso && make run-iso

# Just run (if already built)
make run-iso

# Run simulators (no build needed)
./minios_gui
./minios_simulator
```

### QEMU Controls

- **Ctrl+Alt+G** - Grab/release keyboard and mouse
- **Ctrl+Alt+F** - Toggle fullscreen
- **Ctrl+Alt+2** - QEMU monitor (for debugging)
- **Ctrl+Alt+1** - Return to display

### Project Structure

```
Simulators:     ./minios_gui, ./minios_simulator (ready to run)
Bootable ISO:   make iso → build/minios.iso
Run ISO:        make run-iso
Build script:   ./build_and_run.sh (does everything)
```

## Need Help?

1. **Use the script:** `./build_and_run.sh` does everything
2. **Check tools:** Run `which nasm grub-mkrescue qemu-system-x86_64`
3. **Try simulators:** `./minios_gui` works without building
4. **Read logs:** Look for error messages in terminal
5. **Clean build:** `make clean && make iso`

---

**TL;DR:**

```bash
cd minios
./build_and_run.sh    # Does everything for you!
```

Or manually:

```bash
make clean
make iso
make run-iso
```

Then press A, R, or N keys in QEMU!
