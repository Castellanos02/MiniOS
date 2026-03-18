# Ubuntu Setup Guide for MiniOS

## 🎯 Complete Setup Instructions

This guide will help you set up Ubuntu (or any Debian-based Linux) to build and run MiniOS from scratch.

---

## 📋 Prerequisites

### System Requirements

- **OS:** Ubuntu 20.04+ (also works on Debian, Linux Mint, Pop!_OS)
- **RAM:** 2GB minimum (4GB recommended)
- **Disk:** 5GB free space
- **CPU:** Any x86-64 processor

---

## 🔧 Step 1: Install Build Tools

### Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Install Essential Build Tools

```bash
# GCC compiler and build essentials
sudo apt install -y build-essential

# NASM assembler (for multiboot header)
sudo apt install -y nasm

# Make utility
sudo apt install -y make

# Git (optional, for version control)
sudo apt install -y git
```

**Verify installation:**
```bash
gcc --version
# Should show: gcc (Ubuntu ...) 9.x.x or higher

nasm --version
# Should show: NASM version 2.14.x or higher

make --version
# Should show: GNU Make 4.x
```

---

## 🖥️ Step 2: Install QEMU (Emulator)

### Install QEMU

```bash
sudo apt install -y qemu-system-x86
```

**Verify installation:**
```bash
qemu-system-x86_64 --version
# Should show: QEMU emulator version 4.x or higher
```

---

## 💿 Step 3: Install GRUB Tools (For ISO Creation)

### Install GRUB Utilities

```bash
# GRUB rescue disk creator
sudo apt install -y grub-pc-bin

# ISO creation tools
sudo apt install -y xorriso

# GRUB common files
sudo apt install -y grub-common
```

**Verify installation:**
```bash
grub-mkrescue --version
# Should show: grub-mkrescue (GRUB) 2.x

xorriso --version
# Should show: xorriso 1.x.x
```

---

## 📦 Step 4: Download and Extract MiniOS

### Option A: From Archive

```bash
# Create workspace
mkdir -p ~/minios-workspace
cd ~/minios-workspace

# Extract archive (assuming you have minios.tar.gz)
tar -xzf minios.tar.gz

# Navigate to project
cd minios

# Verify files
ls -la
# Should see: Makefile, kernel/, build/, etc.
```

### Option B: Create Fresh Directory

```bash
mkdir -p ~/minios-workspace/minios
cd ~/minios-workspace/minios

# Copy your kernel files here
# Or extract from provided archive
```

---

## 🏗️ Step 5: Build MiniOS

### Build the CarPlay Version

```bash
cd ~/minios-workspace/minios

# Clean any previous builds
make clean

# Build the CarPlay ISO
make iso-carplay
```

**Expected output:**
```
Building CarPlay-style kernel with app launcher...
✓ Built CarPlay kernel
Creating CarPlay ISO...
✓ Created: build/minios_carplay.iso

🎨 CARPLAY FEATURES:
  ✓ Apple CarPlay-style home screen
  ✓ App launcher with 4 apps
  ✓ Calendar app with scheduled events
  ✓ AI suggestions in calendar
  ✓ Navigation with arrow keys
  ✓ Proactive ML + Memory tracking
  ✓ Works in QEMU and VirtualBox!

Run with: make run-carplay
```

---

## 🚀 Step 6: Run MiniOS

### Run in QEMU

```bash
# From the minios directory
make run-carplay
```

**Or manually:**
```bash
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -boot d
```

**QEMU window should open with your OS!**

---

## 🎮 Step 7: Using MiniOS

### Controls

**Home Screen Navigation:**
- **W / I / ↑** - Move up
- **S / K / ↓** - Move down  
- **A / J / ←** - Move left
- **D / L / →** - Move right
- **Enter / Space** - Open app
- **Q** - Quit

**In Calendar:**
- **Up/Down** - Scroll events
- **A** - Add AI suggestion
- **B/Q** - Back to home

**Proactive Notifications:**
- **Y** - Accept suggestion (adds to calendar)
- **N** - Reject suggestion

---

## 🔍 Troubleshooting

### Issue 1: "gcc: command not found"

**Solution:**
```bash
sudo apt install -y build-essential
```

### Issue 2: "nasm: command not found"

**Solution:**
```bash
sudo apt install -y nasm
```

### Issue 3: "grub-mkrescue: command not found"

**Solution:**
```bash
sudo apt install -y grub-pc-bin grub-common xorriso
```

### Issue 4: "qemu-system-x86_64: command not found"

**Solution:**
```bash
sudo apt install -y qemu-system-x86
```

### Issue 5: Build Errors

**Solution:**
```bash
# Clean and rebuild
make clean
make iso-carplay

# If still failing, check tools:
which gcc nasm make grub-mkrescue
```

### Issue 6: QEMU Opens But Black Screen

**Cause:** ISO not built correctly

**Solution:**
```bash
# Verify ISO exists
ls -lh build/minios_carplay.iso
# Should show ~5MB file

# Rebuild if needed
make clean
make iso-carplay
make run-carplay
```

---

## 📊 All Available Build Targets

### Build Commands

```bash
# Basic bootable version
make iso

# VirtualBox-compatible version
make iso-vbox

# Enhanced version with ML
make iso-enhanced

# CarPlay-style interface (RECOMMENDED)
make iso-carplay

# Clean builds
make clean
```

### Run Commands

```bash
# Run basic version
make run

# Run enhanced version
make run-enhanced

# Run CarPlay version (RECOMMENDED)
make run-carplay
```

### Simulator (No Building Required)

```bash
# Run GUI simulator (easiest)
./minios_gui

# Run with specific activity
./minios_gui_interactive
```

---

## 🖥️ VirtualBox Setup (Optional)

### Install VirtualBox

```bash
sudo apt install -y virtualbox
```

### Create VM

1. **Open VirtualBox**
2. **Click "New"**
3. **Settings:**
   - Name: MiniOS
   - Type: Other
   - Version: Other/Unknown
   - RAM: 256MB
   - No hard disk

4. **Attach ISO:**
   - Settings → Storage
   - Controller: IDE → Empty
   - Disk icon → Choose disk file
   - Select: `build/minios_carplay.iso`

5. **Start VM**

---

## 📁 Project Structure

```
minios/
├── Makefile              # Build system
├── kernel/               # Kernel source files
│   ├── kernel_carplay.c  # CarPlay interface
│   ├── kernel_full.c     # QEMU kernel
│   ├── kernel_vbox.c     # VirtualBox kernel
│   ├── multiboot_header.asm
│   └── linker_multiboot.ld
├── build/                # Compiled binaries (created on build)
│   ├── minios_carplay.iso
│   └── *.o files
├── simulators/           # C simulators
│   ├── minios_gui.c
│   └── minios_gui_interactive.c
├── grub.cfg             # GRUB configuration
└── *.md                 # Documentation files
```

---

## 🎯 Quick Start Summary

**Complete setup in 5 commands:**

```bash
# 1. Install tools
sudo apt update && sudo apt install -y build-essential nasm qemu-system-x86 grub-pc-bin grub-common xorriso

# 2. Navigate to project
cd minios

# 3. Build
make clean && make iso-carplay

# 4. Run
make run-carplay

# 5. Enjoy!
# Navigate with WASD, Enter to open apps, Y/N for notifications
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] `gcc --version` works
- [ ] `nasm --version` works
- [ ] `make --version` works
- [ ] `grub-mkrescue --version` works
- [ ] `qemu-system-x86_64 --version` works
- [ ] `make clean` succeeds
- [ ] `make iso-carplay` creates ISO
- [ ] `make run-carplay` opens QEMU
- [ ] OS boots and shows home screen
- [ ] Can navigate with WASD
- [ ] Can open calendar with Enter
- [ ] Proactive notification appears

---

## 🐧 Other Linux Distributions

### Fedora / Red Hat / CentOS

```bash
sudo dnf install -y gcc nasm make qemu-system-x86 grub2-tools xorriso
```

### Arch Linux

```bash
sudo pacman -S gcc nasm make qemu grub xorriso
```

### openSUSE

```bash
sudo zypper install -y gcc nasm make qemu-x86 grub2 xorriso
```

---

## 🪟 WSL (Windows Subsystem for Linux)

MiniOS can be built in WSL, but QEMU GUI may not work properly.

**Alternative for WSL:**

1. Build ISO in WSL:
```bash
make iso-carplay
```

2. Copy ISO to Windows:
```bash
cp build/minios_carplay.iso /mnt/c/Users/YourName/Downloads/
```

3. Run in Windows with:
   - VirtualBox (Windows version)
   - VMware Player
   - QEMU for Windows

---

## 💡 Tips

### Speed Up Compilation

```bash
# Use parallel builds
make -j4 iso-carplay
```

### Keep Multiple Versions

```bash
# Build all versions
make clean
make iso              # Basic version
make iso-enhanced     # ML version  
make iso-carplay      # CarPlay version

# They'll be in build/ directory
ls build/*.iso
```

### Create Bootable USB (Advanced)

```bash
# WARNING: This will erase the USB drive!
sudo dd if=build/minios_carplay.iso of=/dev/sdX bs=4M
sync

# Replace /dev/sdX with your USB device (check with lsblk)
```

---

## 📞 Quick Reference

**Essential Commands:**

```bash
# Setup
sudo apt install -y build-essential nasm qemu-system-x86 grub-pc-bin grub-common xorriso

# Build
cd minios
make clean
make iso-carplay

# Run
make run-carplay

# Rebuild after code changes
make clean && make iso-carplay && make run-carplay
```

**Your Ubuntu system is now ready to build and run MiniOS!** 🎉
