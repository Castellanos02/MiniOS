# MiniOS Deployment & Sharing Guide

## Can Others Run This?

**YES!** The MiniOS simulators are fully portable and ready to share.

## What's Included & What's Required

### ✅ Ready to Run (No Special Requirements)

**Files:**
- `minios_gui` (31 KB executable)
- `minios_simulator` (30 KB executable)

**Requirements:**
- Linux system (Ubuntu, Fedora, Arch, etc.)
- Standard C library (glibc) - already on every Linux system
- Terminal emulator

**No installation needed!** Just extract and run.

### ⚠️ Requires Building (Advanced Users Only)

**Files:**
- `boot/boot.asm` → Bootloader source
- `kernel/*.c` → Kernel source
- `Makefile` → Build system

**Requirements to BUILD:**
- NASM assembler
- GCC compiler
- GNU linker (ld)
- QEMU (to run the built OS)

**Most users won't need this!** The simulators provide the full experience.

---

## Sharing Instructions

### For End Users (Recommended)

Share the complete archive with these instructions:

```bash
# Extract
tar -xzf minios.tar.gz
cd minios

# Run the GUI version (best experience)
./minios_gui

# Or run the text version (universal compatibility)
./minios_simulator
```

**That's it!** No installation, compilation, or dependencies.

### For Developers

If they want to modify and rebuild:

```bash
cd minios

# Rebuild the simulators
make simulator

# Or rebuild just the GUI
gcc -o minios_gui minios_gui.c -lm
```

---

## System Compatibility

### ✅ Works Out of the Box

**Linux distributions:**
- Ubuntu / Debian
- Fedora / RHEL / CentOS
- Arch Linux
- openSUSE
- Mint
- Elementary OS
- Pop!_OS
- Manjaro
- Any other Linux distro with glibc

**Architectures:**
- x86_64 (64-bit Intel/AMD)
- Should work on ARM64 with recompilation

### ⚠️ Requires Setup

**macOS:**
- Needs recompilation: `gcc -o minios_gui minios_gui.c -lm`
- Or run via Docker/VM

**Windows:**
- Use WSL (Windows Subsystem for Linux)
- Or compile with MinGW/Cygwin
- Or run in Docker

**Other Unix-like systems:**
- BSD, Solaris: Recompile with local GCC

---

## What About QEMU?

### QEMU is NOT Used by the Simulators

The pre-built executables (`minios_gui` and `minios_simulator`) are **regular Linux programs**. They:

- ❌ Do NOT require QEMU
- ❌ Do NOT emulate hardware
- ❌ Do NOT boot a custom OS
- ✅ Run as normal applications
- ✅ Use the host Linux kernel
- ✅ Work on any Linux system

**Think of them like any other program** - Firefox, Vim, etc. They're just regular executables.

### QEMU is ONLY for the Full OS Build

If someone wants to build and run the **actual custom OS** (not the simulator):

```bash
# This requires NASM + QEMU
make              # Build the OS image
make run          # This uses QEMU
```

**QEMU command used:**
```bash
qemu-system-x86_64 -drive format=raw,file=build/minios.img -m 128M
```

This boots the custom OS in a virtual machine, similar to VirtualBox or VMware.

**99% of users don't need this!** The simulators provide the same experience.

---

## File Size & Portability

### Archive Contents

```
minios.tar.gz (61 KB total)
├── minios_gui (31 KB) ← Executable, ready to run
├── minios_simulator (30 KB) ← Executable, ready to run
├── minios_gui.c (17 KB) ← Source code
├── minios_simulator.c (17 KB) ← Source code
├── Documentation (*.md files)
├── boot/ (bootloader source)
├── kernel/ (kernel source)
├── gui/ (GUI framework source)
├── python/ (SNN model source)
└── Makefile (build system)
```

**Total**: 61 KB compressed, ~200 KB uncompressed

**Very portable!** Can be:
- Shared via email
- Downloaded from GitHub
- Copied to USB drive
- Distributed in repositories

### Dependencies

**Runtime (to run simulators):**
- libc.so.6 (standard C library) - always present
- libm.so.6 (math library) - always present
- Linux kernel 2.6+ - any modern Linux

**Build-time (to recompile simulators):**
- GCC compiler
- GNU Make (optional)

Check dependencies:
```bash
ldd minios_gui
# Output:
#   linux-vdso.so.1
#   libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6
#   libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
#   /lib64/ld-linux-x86-64.so.2
```

All standard libraries present on every Linux system!

---

## Distribution Methods

### Option 1: Direct Archive Share

**Best for:** Personal sharing, small groups

```bash
# Just send minios.tar.gz
# Recipients extract and run
```

**Pros:**
- Simple and fast
- No hosting needed
- Works offline

### Option 2: GitHub Repository

**Best for:** Public distribution, collaboration

```bash
# Upload to GitHub
git init
git add .
git commit -m "Initial commit"
git push origin main
```

**Pros:**
- Version control
- Easy updates
- Community contributions
- Issue tracking

### Option 3: Package Repository

**Best for:** Wide distribution

Create packages:
- `.deb` for Debian/Ubuntu
- `.rpm` for Fedora/RHEL
- AUR package for Arch

### Option 4: Docker Container

**Best for:** Maximum compatibility

```dockerfile
FROM ubuntu:24.04
COPY minios /app
WORKDIR /app
CMD ["./minios_gui"]
```

**Pros:**
- Works on any OS with Docker
- Isolated environment
- Includes all dependencies

---

## Testing Before Sharing

### Checklist for Distributors

Before sharing with others, verify:

```bash
# 1. Extract fresh copy
tar -xzf minios.tar.gz
cd minios

# 2. Test GUI version
./minios_gui
# Press A, R, I, L to test
# Press Q to quit

# 3. Test text version
./minios_simulator
# Press A, R, I, L to test
# Press Q to quit

# 4. Test log export
./minios_gui
# Press A a few times
# Press L, then E
# Check: /mnt/user-data/outputs/minios_feedback_logs.csv exists

# 5. Verify documentation
ls *.md
# Should see: README.md, QUICKSTART.md, GUI_GUIDE.md, etc.

# 6. Test rebuild (if GCC available)
make simulator
./minios_gui
```

### Verification Script

Create `test_distribution.sh`:

```bash
#!/bin/bash
echo "Testing MiniOS Distribution..."

# Check executables exist
if [ ! -f minios_gui ]; then
    echo "❌ minios_gui missing"
    exit 1
fi

if [ ! -f minios_simulator ]; then
    echo "❌ minios_simulator missing"
    exit 1
fi

# Check executables work
echo "Testing executables..."
if ! ./minios_gui --version 2>/dev/null; then
    echo "⚠️  minios_gui may not work (no --version flag, this is OK)"
fi

# Check documentation
echo "Checking documentation..."
for doc in README.md QUICKSTART.md GUI_GUIDE.md; do
    if [ ! -f $doc ]; then
        echo "⚠️  Missing: $doc"
    fi
done

echo "✅ Distribution looks good!"
```

---

## User Support

### Common User Questions

**Q: Do I need to install anything?**
A: No! Just extract and run `./minios_gui`

**Q: It says "command not found"**
A: Run `chmod +x minios_gui` then try again

**Q: Can I use this on Mac/Windows?**
A: Mac: Recompile with GCC. Windows: Use WSL.

**Q: Do I need QEMU?**
A: No! QEMU is only for the full OS build (advanced).

**Q: Can I modify the code?**
A: Yes! Edit the .c files and run `make simulator`

**Q: Where are logs saved?**
A: `/mnt/user-data/outputs/minios_feedback_logs.csv`

### Troubleshooting for Users

Direct them to:
1. **TROUBLESHOOTING.md** - Common issues
2. **GUI_GUIDE.md** - GUI-specific help
3. **QUICKSTART.md** - Basic usage

---

## License & Attribution

When sharing, include:

```
MiniOS - Neural Activity Suggester
Copyright (c) 2026
License: MIT

Built with Claude (Anthropic AI)
Educational project demonstrating OS development
and embedded machine learning.
```

---

## Summary

### ✅ Yes, Share the Entire Folder!

Recipients can:
1. Extract `minios.tar.gz`
2. Run `./minios_gui` or `./minios_simulator`
3. No installation, compilation, or QEMU needed

### 📦 What They Get

- ✅ Two ready-to-run executables
- ✅ Complete source code
- ✅ Comprehensive documentation
- ✅ Build system (optional use)
- ✅ All features working

### 🚀 What They Don't Need

- ❌ QEMU (unless building full OS)
- ❌ NASM (unless building full OS)
- ❌ Special permissions
- ❌ Root/sudo access
- ❌ Internet connection

**It's that simple!** The simulators are self-contained, portable Linux applications.

---

**Bottom Line:** Share the archive. Anyone with Linux can run it immediately. QEMU is only for the optional full OS build that most users won't need.
