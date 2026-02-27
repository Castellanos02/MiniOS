# MiniOS - Complete Setup & Build Guide

**Welcome to MiniOS!** This is your complete guide to building, running, and understanding your custom operating system with embedded neural network capabilities.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start) - Get running in 5 minutes
2. [What is MiniOS?](#what-is-minios) - Understanding the project
3. [Available Versions](#available-versions) - Choose your approach
4. [Complete Build Process](#complete-build-process) - From source to bootable
5. [Running in QEMU](#running-in-qemu) - Linux/WSL virtualization
6. [Running in VirtualBox](#running-in-virtualbox) - Cross-platform VM
7. [Project Architecture](#project-architecture) - Technical overview
8. [Troubleshooting](#troubleshooting) - Common issues solved
9. [Documentation Index](#documentation-index) - Find specific guides

---

## 🚀 Quick Start

### Fastest Way (Simulators - No Building Required!)

```bash
cd minios

# Option 1: CarPlay-style GUI (recommended)
./minios_gui

# Option 2: Text interface
./minios_simulator
```

**That's it!** The simulators work immediately with all features.

### Build Bootable ISO (QEMU)

```bash
cd minios
make clean
make iso
make run-iso
```

### Build for VirtualBox

```bash
cd minios
make clean
make iso-vbox
# Then attach build/minios_vbox.iso in VirtualBox
```

---

## 🎯 What is MiniOS?

MiniOS is a **custom operating system** built from scratch that demonstrates:

### Core OS Concepts
- ✅ **Custom kernel** written in C and Assembly
- ✅ **Bootloader integration** (GRUB multiboot)
- ✅ **Memory management** (paging, segmentation)
- ✅ **Hardware interaction** (VGA text mode, keyboard I/O)
- ✅ **Real-time processing** (event-driven architecture)

### Machine Learning Integration
- ✅ **Embedded neural network** (Spiking Neural Network)
- ✅ **Activity suggestion system** (20 different activities)
- ✅ **Learning from feedback** (Accept/Reject/Next)
- ✅ **Performance monitoring** (accuracy tracking, latency)

### User Interface
- ✅ **Graphical interface** (colorful text-based GUI)
- ✅ **Interactive controls** (keyboard input A/R/N)
- ✅ **Visual feedback** (notifications, status indicators)
- ✅ **Real-time updates** (live activity suggestions)

---

## 📦 Available Versions

MiniOS comes in **three versions**, each serving different purposes:

### 1. Simulators (Ready to Run) ⭐ **RECOMMENDED**

**Files:** `minios_gui`, `minios_simulator`

**Features:**
- ✅ No building required - run immediately
- ✅ All 20 activities available
- ✅ Complete ML system with learning
- ✅ Full keyboard support (A/R/N, I/L, Q)
- ✅ CSV logging and export
- ✅ Performance metrics
- ✅ Easy debugging with standard tools

**Use when:**
- Developing and testing
- Demonstrating functionality
- Portfolio/demo purposes
- You want ALL features working

**Run:**
```bash
./minios_gui        # Beautiful CarPlay-style interface
./minios_simulator  # Classic text interface
```

### 2. QEMU Bootable ISO

**File:** `build/minios.iso` (after building)

**Features:**
- ✅ Boots from ISO in QEMU
- ✅ Real bootloader (GRUB)
- ✅ 8 activities
- ✅ Keyboard support (polling)
- ✅ Proves it's a real OS

**Use when:**
- Testing bootable capabilities
- Running in QEMU/KVM
- Educational purposes (learning boot process)

**Build & Run:**
```bash
make iso
make run-iso
```

### 3. VirtualBox Bootable ISO

**File:** `build/minios_vbox.iso` (after building)

**Features:**
- ✅ Boots in VirtualBox
- ✅ Works on Windows/Mac/Linux
- ✅ 8 activities
- ✅ Keyboard support (polling)
- ✅ Easy to share and demo

**Use when:**
- Demonstrating on any platform
- VirtualBox is your preferred VM
- Sharing with others (cross-platform)

**Build:**
```bash
make iso-vbox
```

---

## 🔨 Complete Build Process

### Prerequisites

#### Required Tools

```bash
# Ubuntu/Debian/WSL
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    nasm \
    gcc \
    binutils \
    grub-pc-bin \
    xorriso \
    mtools \
    qemu-system-x86

# Fedora/RHEL
sudo dnf install -y gcc nasm grub2-tools xorriso mtools qemu-system-x86

# Arch Linux
sudo pacman -S gcc nasm grub xorriso mtools qemu
```

#### Verify Installation

```bash
# Check all tools are available
gcc --version
nasm -version
ld --version
grub-mkrescue --version
qemu-system-x86_64 --version
```

### Build Steps

#### 1. Clean Previous Build

```bash
cd minios
make clean
```

This removes:
- `build/` directory
- Compiled object files
- Previous ISO images

#### 2. Build Kernel

The kernel is built automatically when you run `make iso`, but here's what happens:

**Compile Assembly:**
```bash
# Multiboot header
nasm -f elf32 kernel/multiboot_header.asm -o build/multiboot_header.o
```

**Compile C Code:**
```bash
# Main kernel
gcc -m32 -ffreestanding -fno-stack-protector -nostdlib -Ikernel \
    -c kernel/kernel_full.c -o build/kernel_full.o
```

**Link Kernel:**
```bash
# Create ELF executable
ld -m elf_i386 -T kernel/linker_multiboot.ld \
    build/multiboot_header.o build/kernel_full.o \
    -o build/minios.bin
```

#### 3. Build ISO

**For QEMU:**
```bash
make iso
```

This:
1. Creates `build/isodir/` structure
2. Copies kernel to `build/isodir/boot/minios.bin`
3. Copies GRUB config to `build/isodir/boot/grub/grub.cfg`
4. Runs `grub-mkrescue` to create bootable ISO
5. Outputs: `build/minios.iso` (4-5 MB)

**For VirtualBox:**
```bash
make iso-vbox
```

Same process but uses `kernel_vbox.c` (optimized for VirtualBox).
Outputs: `build/minios_vbox.iso`

#### 4. Verify Build

```bash
# Check ISO was created
ls -lh build/minios.iso

# Verify it's bootable
file build/minios.iso
# Should show: "ISO 9660 CD-ROM filesystem data (DOS/MBR boot sector)"
```

### Build Targets Reference

```bash
make                    # Build full OS (default target)
make iso                # Build QEMU ISO
make iso-vbox           # Build VirtualBox ISO
make simulator          # Build both simulators
make minios_gui         # Build GUI simulator only
make minios_simulator   # Build text simulator only
make clean              # Remove all build artifacts
make run-iso            # Build and run QEMU ISO
make run-gui            # Build and run GUI simulator
make run-sim            # Build and run text simulator
make help               # Show all available targets
```

---

## 🖥️ Running in QEMU

### Method 1: Using Makefile (Easiest)

```bash
make run-iso
```

### Method 2: Manual Command

```bash
qemu-system-x86_64 -cdrom build/minios.iso -m 256M -boot d
```

### QEMU Options Explained

```bash
qemu-system-x86_64 \
    -cdrom build/minios.iso \  # Boot from ISO
    -m 256M \                  # 256MB RAM
    -boot d \                  # Boot from CD-ROM
    -serial stdio              # Optional: serial output to console
```

### Common QEMU Commands

```bash
# Basic boot
qemu-system-x86_64 -cdrom build/minios.iso -m 256M

# With more memory
qemu-system-x86_64 -cdrom build/minios.iso -m 512M

# Fullscreen
qemu-system-x86_64 -cdrom build/minios.iso -m 256M -full-screen

# With debugging
qemu-system-x86_64 -cdrom build/minios.iso -m 256M -serial stdio -d int
```

### QEMU Keyboard Controls

- **Ctrl+Alt+G** - Release mouse/keyboard from QEMU
- **Ctrl+Alt+F** - Toggle fullscreen
- **Ctrl+Alt+2** - Switch to QEMU monitor
- **Ctrl+Alt+1** - Switch back to display

### Expected QEMU Boot Sequence

1. **QEMU window opens** (800x600 black screen)
2. **SeaBIOS messages** (brief, 1-2 seconds)
3. **GRUB menu appears** (blue background)
   ```
   GNU GRUB
   
   MiniOS - Neural Activity Suggester
   MiniOS - Safe Mode
   ```
4. **After 3 seconds** (or press Enter): MiniOS boots
5. **GUI loads** - Colorful interface with:
   - Blue header bar
   - Cyan activity panel
   - Controls: [A] Accept [R] Reject [N] Next
   - Status indicators

### Using MiniOS in QEMU

Once booted:
- **Press A** - Accept current activity (green notification)
- **Press R** - Reject current activity (red notification)
- **Press N** - Load next activity immediately

### Troubleshooting QEMU

**Issue: Black screen**
- Wait 5-10 seconds for boot
- Try: `qemu-system-x86_64 -cdrom build/minios.iso -m 256M -vga std`

**Issue: Keyboard doesn't work**
- Click inside QEMU window to capture input
- Press Ctrl+Alt+G to release/recapture

**Issue: "No bootable device"**
- Rebuild: `make clean && make iso`
- Verify ISO exists: `ls -lh build/minios.iso`

---

## 📦 Running in VirtualBox

### Step-by-Step Setup

#### 1. Install VirtualBox

**Windows/Mac:**
- Download from: https://www.virtualbox.org/wiki/Downloads
- Install "Windows hosts" or "Mac OS X hosts" version
- Version 7.0 or newer recommended

**Linux:**
```bash
sudo apt-get install virtualbox
```

#### 2. Build VirtualBox ISO

```bash
cd minios
make clean
make iso-vbox
```

This creates: `build/minios_vbox.iso` (~5 MB)

#### 3. Create Virtual Machine

**Using VirtualBox GUI:**

1. **Open VirtualBox**

2. **Click "New"** (or Machine → New)

3. **Virtual Machine Settings:**
   - **Name:** `MiniOS`
   - **Type:** `Linux`
   - **Version:** `Other Linux (64-bit)`
   - **Click "Next"**

4. **Hardware:**
   - **Memory:** `256 MB` (minimum 128 MB)
   - **Processors:** `1 CPU`
   - **Click "Next"**

5. **Virtual Hard Disk:**
   - **Select:** "Do not add a virtual hard disk"
   - **Click "Next"**
   - Confirm the warning

6. **Click "Finish"**

#### 4. Attach ISO

1. **Right-click** the "MiniOS" VM → **Settings**

2. **Go to "Storage" tab**

3. **Click "Empty"** under IDE Controller

4. **Click the disk icon** (on the right)

5. **Choose "Choose a disk file..."**

6. **Navigate to:** `minios/build/minios_vbox.iso`

7. **Click "Open"** then **"OK"**

#### 5. Start VM

- **Double-click "MiniOS"** VM
- Or: Right-click → Start → Normal Start

#### 6. Boot Process

1. VirtualBox window opens
2. GRUB menu appears
3. Select "MiniOS - Neural Activity Suggester"
4. GUI loads with colorful interface
5. Press A/R/N to interact!

### VirtualBox Command Line Setup

Alternatively, use command line:

```bash
# Create VM
VBoxManage createvm --name "MiniOS" --ostype "Linux_64" --register

# Configure
VBoxManage modifyvm "MiniOS" \
    --memory 256 \
    --vram 16 \
    --boot1 dvd \
    --boot2 none

# Add storage controller
VBoxManage storagectl "MiniOS" --name "IDE" --add ide

# Attach ISO
VBoxManage storageattach "MiniOS" \
    --storagectl "IDE" \
    --port 0 \
    --device 0 \
    --type dvddrive \
    --medium "$(pwd)/build/minios_vbox.iso"

# Start VM
VBoxManage startvm "MiniOS" --type gui
```

### Automated Setup Script

Use the provided script:

```bash
./setup_virtualbox.sh
```

This automates the entire VM creation process.

### VirtualBox Keyboard Controls

- **Right Ctrl** - Host key (release mouse/keyboard)
- **Right Ctrl + F** - Toggle fullscreen
- **Right Ctrl + E** - Take screenshot

### Using MiniOS in VirtualBox

Once booted:
- **Click inside VM** to capture keyboard
- **Press A** - Accept activity (green notification)
- **Press R** - Reject activity (red notification)
- **Press N** - Next activity

### Troubleshooting VirtualBox

**Issue: "Critical error" on boot**
- Remove virtual hard disk in Settings → Storage
- Ensure only DVD drive (with ISO) is present

**Issue: Keyboard doesn't work**
- Click inside VM window
- Press Right Ctrl to release/recapture

**Issue: Black screen**
- Try different graphics controller:
  - Settings → Display → Graphics Controller → VMSVGA

**Issue: ISO not found (WSL users)**
- Copy ISO to Windows:
  ```bash
  cp build/minios_vbox.iso /mnt/c/Users/USERNAME/Downloads/
  ```
- Then browse to `C:\Users\USERNAME\Downloads\minios_vbox.iso`

---

## 🏗️ Project Architecture

### Directory Structure

```
minios/
├── boot/                    # Bootloader code
│   └── boot.asm            # Custom bootloader (optional)
├── kernel/                  # Kernel source
│   ├── multiboot_header.asm # GRUB multiboot header
│   ├── kernel_full.c        # Main kernel (QEMU)
│   ├── kernel_vbox.c        # VirtualBox kernel
│   ├── linker_multiboot.ld  # Linker script
│   ├── stdint.h            # Standard types
│   └── stddef.h            # Standard definitions
├── gui/                     # GUI components
│   └── gui.c               # VGA graphics
├── python/                  # ML runtime
│   └── python_runtime.c    # Neural network
├── build/                   # Build output
│   ├── minios.iso          # QEMU bootable ISO
│   ├── minios_vbox.iso     # VirtualBox bootable ISO
│   ├── minios.bin          # Kernel binary
│   └── isodir/             # ISO directory structure
├── minios_gui.c            # GUI simulator source
├── minios_simulator.c      # Text simulator source
├── minios_gui              # GUI simulator (executable)
├── minios_simulator        # Text simulator (executable)
├── Makefile                # Build system
├── grub.cfg                # GRUB configuration
└── *.md                    # Documentation
```

### Boot Process

```
1. Power On
   ↓
2. BIOS/UEFI
   ↓
3. GRUB Bootloader
   - Reads grub.cfg
   - Shows menu
   - Loads kernel
   ↓
4. Multiboot Header
   - Verified by GRUB
   - Kernel location identified
   ↓
5. Kernel Entry (_start)
   - Stack initialized
   - Multiboot magic checked
   ↓
6. kernel_main()
   - VGA initialized
   - GUI drawn
   - Main loop started
   ↓
7. Running OS
   - Polls keyboard
   - Updates display
   - Processes input
```

### Key Components

**Multiboot Header** (`multiboot_header.asm`):
- Magic numbers for GRUB
- Kernel entry point
- Stack setup

**Kernel** (`kernel_full.c` / `kernel_vbox.c`):
- VGA text mode graphics
- Keyboard polling
- Activity suggestion system
- Main event loop

**GUI** (in kernel):
- Box drawing with Unicode characters
- Color management
- Text rendering
- Layout system

**Keyboard Input**:
- Port I/O (0x60 data, 0x64 status)
- Scancode to ASCII conversion
- Polling-based (no interrupts)

### Memory Layout

```
0x00000000 - 0x00100000   Real mode memory, BIOS
0x00100000 - 0x0010FFFF   Kernel code (.text)
0x00110000 - 0x0011FFFF   Kernel data (.data, .bss)
0x000B8000 - 0x000B8FA0   VGA text buffer
Stack grows down from high memory
```

---

## 🔧 Troubleshooting

### Build Issues

**Error: "nasm: command not found"**
```bash
sudo apt-get install nasm
```

**Error: "grub-mkrescue: command not found"**
```bash
sudo apt-get install grub-pc-bin xorriso mtools
```

**Error: "unknown type name 'size_t'"**
- Already fixed - custom headers included
- If issue persists: `make clean && make iso`

### Runtime Issues

**Black screen in QEMU/VirtualBox**
- Wait 10 seconds for boot
- Check ISO exists: `ls -lh build/minios.iso`
- Rebuild: `make clean && make iso`

**Keyboard not responding**
- Click inside VM window
- Try pressing keys multiple times
- Check if blinking cursor appears (bottom-right *)

**Triple fault / VM crashes**
- Use VirtualBox version: `make iso-vbox`
- Remove virtual hard disk from VM
- Ensure only DVD/CD drive present

### WSL-Specific Issues

**QEMU can't find ISO**
- Use absolute path:
  ```bash
  qemu-system-x86_64 -cdrom "$(pwd)/build/minios.iso" -m 256M
  ```

**VirtualBox can't find ISO**
- Copy to Windows:
  ```bash
  cp build/minios_vbox.iso /mnt/c/Users/USERNAME/Downloads/
  ```
- Browse to `C:\Users\USERNAME\Downloads\minios_vbox.iso` in VirtualBox

---

## 📚 Documentation Index

Your `minios.tar.gz` includes comprehensive documentation:

### Getting Started
- **README.md** - Project overview and quick start
- **QUICKSTART.md** - 5-minute getting started guide
- **MASTER_GUIDE.md** - This file (complete reference)

### Building
- **BUILD_GUIDE.md** - Detailed build instructions
- **Makefile** - Build system with comments

### Running
- **VIRTUALBOX_GUIDE.md** - Complete VirtualBox setup
- **QEMU_TROUBLESHOOTING.md** - QEMU-specific issues
- **setup_virtualbox.sh** - Automated VM creation

### Technical Documentation
- **ARCHITECTURE.md** - System architecture deep dive
- **TECHNICAL_SPEC.md** - Technical specifications
- **PROJECT_SUMMARY.md** - High-level project summary

### GUI & Interface
- **GUI_GUIDE.md** - CarPlay-style GUI documentation
- **GRUB_GUI_GUIDE.md** - Bootable GUI features
- **INTERFACE_COMPARISON.md** - Simulator vs bootable

### Boot Process
- **GRUB_GUIDE.md** - GRUB multiboot integration
- **BOOT_DEBUG.md** - Boot process debugging
- **BOOTLOADER_SOLUTION.md** - Custom vs GRUB bootloaders

### Keyboard & Input
- **KEYBOARD_SUPPORT.md** - Interrupt vs polling
- **POLLING_UPDATE.md** - Universal polling implementation

### Troubleshooting
- **TROUBLESHOOTING.md** - Common issues and solutions
- **STEP_BY_STEP_FIX.md** - Systematic problem solving
- **VBOX_FIX.md** - VirtualBox triple fault fix
- **QUICK_FIX.md** - Quick solutions

### Deployment
- **DEPLOYMENT_GUIDE.md** - Sharing and distribution
- **FINAL_SOLUTION.md** - When things don't work

---

## 🎯 Recommended Workflows

### For Development
1. Use `./minios_gui` or `./minios_simulator`
2. Modify code
3. Recompile: `gcc -o minios_gui minios_gui.c -lm`
4. Test immediately

### For Demonstration
1. Build VirtualBox ISO: `make iso-vbox`
2. Create VM (or use `./setup_virtualbox.sh`)
3. Show it boots and runs
4. Show keyboard interaction (A/R/N)

### For Portfolio
Show all three versions:
1. **Simulators** - Full features, easy to use
2. **QEMU ISO** - Proves bootability
3. **VirtualBox ISO** - Cross-platform demo

### For Learning
1. Read ARCHITECTURE.md
2. Study kernel source code
3. Experiment with modifications
4. Test in simulators first
5. Build bootable version to verify

---

## 📞 Need Help?

1. Check **TROUBLESHOOTING.md** for common issues
2. Run `./diagnose.sh` for system diagnostics
3. Check specific guides in documentation index
4. Use `make help` to see all build targets

---

## ✅ Success Checklist

- [ ] Simulators run and respond to keyboard
- [ ] ISO builds without errors
- [ ] QEMU boots and shows GUI
- [ ] VirtualBox VM created and runs
- [ ] Keyboard works (A/R/N keys)
- [ ] Activities change and show notifications
- [ ] Blinking indicator visible (bottom-right)

---

## 🎉 You're All Set!

Your MiniOS is ready to:
- ✅ Boot from ISO in QEMU and VirtualBox
- ✅ Display beautiful graphical interface
- ✅ Accept keyboard input (A/R/N)
- ✅ Suggest activities intelligently
- ✅ Demonstrate OS and ML concepts

**Start with the simplest:** `./minios_gui` and enjoy your custom OS! 🚀
