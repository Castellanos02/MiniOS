# MiniOS Build Guide

## Overview

MiniOS has **two separate build paths**:

1. **Simulators** (GUI & Text) - No special tools needed ✅
2. **Full OS** (Bootable image) - Requires NASM + QEMU ⚠️

Most users only need the simulators!

---

## Quick Start: Pre-built Simulators (Recommended)

The easiest way to use MiniOS:

```bash
cd minios

# Run the CarPlay-style GUI
./minios_gui

# Or run the text interface
./minios_simulator
```

**No compilation needed!** These are already built and ready to run.

---

## Building Simulators from Source

If you want to recompile the simulators:

### Requirements
- GCC compiler
- Standard C library (glibc)
- Make (optional)

### Build Commands

**Using Make:**
```bash
make simulator          # Builds both
make minios_gui         # Just GUI
make minios_simulator   # Just text
```

**Manual compilation:**
```bash
# GUI version
gcc -o minios_gui minios_gui.c -lm -Wall

# Text version
gcc -o minios_simulator minios_simulator.c -lm -Wall
```

---

## Building the Full OS

This creates a bootable OS image that runs in QEMU.

### Requirements

**Essential:**
- NASM assembler (2.14+)
- GCC compiler (9.0+)
- GNU binutils (ld, as)
- GNU Make

**To run:**
- QEMU x86_64 emulator (4.0+)

### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential nasm qemu-system-x86
```

**Fedora/RHEL:**
```bash
sudo dnf install -y gcc nasm ld qemu-system-x86
```

**Arch Linux:**
```bash
sudo pacman -S base-devel nasm qemu-arch-extra
```

**macOS (Homebrew):**
```bash
brew install nasm qemu
```

### Build Process

```bash
cd minios

# Clean previous builds
make clean

# Build the full OS
make

# This creates:
# - build/boot.bin (bootloader, 512 bytes)
# - build/kernel.bin (kernel)
# - build/minios.img (full OS image, 1MB)
```

### Running in QEMU

```bash
# Run the OS
make run

# Or manually:
qemu-system-x86_64 -drive format=raw,file=build/minios.img -m 128M
```

### Debug Mode

```bash
# Terminal 1: Start QEMU in debug mode
make debug

# Terminal 2: Attach GDB
gdb
(gdb) target remote :1234
(gdb) break kernel_main
(gdb) continue
```

---

## Build Architecture

### Simulator Build (Simple)

```
Source Files                 Compilation              Output
────────────────            ──────────────           ────────────
minios_gui.c         →      gcc -o minios_gui  →    minios_gui
minios_simulator.c   →      gcc -o ...         →    minios_simulator
```

**Dependencies:** Just GCC and libc (standard on all Linux)

### Full OS Build (Complex)

```
Stage 1: Bootloader
────────────────────────────────────────
boot/boot.asm  →  nasm -f bin  →  build/boot.bin (512 bytes)

Stage 2: Kernel Assembly
────────────────────────────────────────
kernel/interrupts.asm  →  nasm -f elf64  →  build/interrupts.o

Stage 3: Kernel C Code
────────────────────────────────────────
kernel/kernel_main.c   →  gcc -ffreestanding  →  build/kernel_main.o
gui/gui.c              →  gcc -ffreestanding  →  build/gui.o
python/python_runtime.c →  gcc -ffreestanding  →  build/python_runtime.o

Stage 4: Linking
────────────────────────────────────────
All .o files  →  ld -T linker.ld  →  build/kernel.bin

Stage 5: Image Creation
────────────────────────────────────────
boot.bin + kernel.bin  →  cat + truncate  →  build/minios.img
```

**Dependencies:** NASM, GCC, ld, custom headers (stdint.h, stddef.h)

---

## Custom Headers for Freestanding Build

The kernel uses **freestanding compilation** (`-ffreestanding -nostdlib`), which means it can't use standard library headers.

We provide custom headers in each component directory:

**kernel/stdint.h** - Fixed-width integer types
```c
typedef unsigned char      uint8_t;
typedef unsigned short     uint16_t;
typedef unsigned int       uint32_t;
typedef unsigned long long uint64_t;
// etc.
```

**kernel/stddef.h** - Standard definitions
```c
typedef unsigned long size_t;
typedef long ptrdiff_t;
#define NULL ((void*)0)
```

These headers are automatically included via `-Ikernel`, `-Igui`, `-Ipython` flags.

---

## Common Build Issues

### Issue: "NASM not found"

**Error:**
```
ERROR: NASM assembler not found
```

**Solution 1 (Install NASM):**
```bash
sudo apt-get install nasm
```

**Solution 2 (Use simulators instead):**
```bash
make simulator
./minios_gui
```

The simulators provide the same experience without needing NASM!

### Issue: "no include path for stdint.h"

**Error:**
```
error: no include path in which to search for stdint.h
```

**Solution:**
This should be fixed in the latest version. The custom headers in `kernel/`, `gui/`, and `python/` directories provide these types.

If you still see this error:
```bash
# Verify headers exist
ls kernel/stdint.h kernel/stddef.h

# Rebuild cleanly
make clean
make
```

### Issue: "undefined reference to 'memset'"

**Error:**
```
undefined reference to 'memset', 'memcpy', etc.
```

**Solution:**
For freestanding kernels, you need to implement these functions yourself or use compiler built-ins. Our kernel avoids these functions.

### Issue: QEMU not found

**Error:**
```
make: qemu-system-x86_64: Command not found
```

**Solution:**
```bash
sudo apt-get install qemu-system-x86
```

Or use the simulators which don't need QEMU.

---

## Build Targets Reference

```bash
make                    # Build full OS (needs NASM)
make clean              # Remove all build artifacts
make run                # Build and run in QEMU
make debug              # Build and run in debug mode
make simulator          # Build both simulators (no NASM)
make minios_gui         # Build GUI simulator only
make minios_simulator   # Build text simulator only
make run-gui            # Build and run GUI
make run-sim            # Build and run text
make help               # Show all targets
```

---

## Compilation Flags Explained

### Simulator Compilation
```bash
gcc -o minios_gui minios_gui.c -lm -Wall
```

- No special flags needed
- `-lm`: Link math library (for `expf()`)
- `-Wall`: Enable all warnings
- Uses standard C library

### Kernel Compilation
```bash
gcc -ffreestanding -fno-stack-protector -fno-pic -mno-red-zone \
    -nostdlib -Ikernel -Wall -Wextra -O2 -m64 \
    -c kernel/kernel_main.c -o build/kernel_main.o
```

**Flags explained:**
- `-ffreestanding`: Not hosted environment (no OS)
- `-fno-stack-protector`: No stack canaries
- `-fno-pic`: No position-independent code
- `-mno-red-zone`: No red zone (x86_64 requirement)
- `-nostdlib`: Don't link standard library
- `-Ikernel`: Include custom headers from kernel/
- `-m64`: Generate 64-bit code
- `-O2`: Optimization level 2

---

## Verifying Your Build

### Test Simulators
```bash
# Test GUI
./minios_gui
# Press A, R, I, L, Q to test all features
# Should exit cleanly with Q

# Test text mode
./minios_simulator
# Same testing process
```

### Test Full OS
```bash
# Run in QEMU
make run

# Expected output:
# - QEMU window opens
# - "MiniOS v1.0" appears
# - "Initializing..." messages
# - Eventually shows GUI or kernel panic if something's wrong
```

### Check Built Files
```bash
ls -lh build/
# Should see:
#   boot.bin (512 bytes)
#   kernel.bin (~50 KB)
#   minios.img (1 MB)
#   *.o files (object files)
```

---

## Clean Build

If you encounter issues:

```bash
# Full clean
make clean
rm -rf build/
rm -f minios_gui minios_simulator

# Rebuild simulators
make simulator

# Or rebuild full OS (if you have NASM)
make
```

---

## Cross-Platform Notes

### Linux
✅ Native platform - everything works out of the box

### macOS
- Simulators: Recompile with `gcc -o minios_gui minios_gui.c -lm`
- Full OS: Install NASM and QEMU via Homebrew
- Note: Paths may differ (`/usr/local/bin/nasm`)

### Windows
- Simulators: Use WSL (Windows Subsystem for Linux)
- Full OS: Use WSL with NASM and QEMU installed
- Alternative: Use Docker container

### BSD/Other Unix
- May need minor adjustments
- Compiler flags might differ
- Test simulators first

---

## Performance Optimization

### Faster Compilation
```bash
# Use parallel make
make -j$(nproc)

# Skip warnings
make CFLAGS="-O2 -w"
```

### Smaller Binary
```bash
# Strip symbols
strip minios_gui
strip minios_simulator

# Result: ~15 KB instead of ~30 KB
```

### Optimize for Speed
```bash
gcc -o minios_gui minios_gui.c -lm -O3 -march=native
```

---

## Development Workflow

### Modifying Simulators
```bash
# 1. Edit source
vim minios_gui.c

# 2. Recompile
make minios_gui

# 3. Test
./minios_gui
```

### Modifying Kernel
```bash
# 1. Edit source
vim kernel/kernel_main.c

# 2. Rebuild
make clean
make

# 3. Test in QEMU
make run
```

### Quick Iteration
```bash
# Watch for changes and rebuild
while inotifywait -e modify *.c; do
    make simulator
done
```

---

## Troubleshooting Tips

1. **Always start with `make clean`** if builds fail
2. **Check NASM version:** `nasm -v` (need 2.14+)
3. **Check GCC version:** `gcc --version` (need 9.0+)
4. **Verify headers exist:** `ls kernel/std*.h`
5. **Test simulators first** - they're simpler to debug
6. **Read error messages carefully** - they usually point to the issue
7. **Check file permissions:** `chmod +x minios_gui`

---

## Next Steps

After successful build:

1. ✅ Run the simulators - Get familiar with the interface
2. ✅ Modify activities - Edit activity lists in source
3. ✅ Customize colors - Change color schemes
4. ✅ Add features - Extend the code
5. ✅ Build full OS - Try QEMU if you have NASM

---

## Additional Resources

- **QUICKSTART.md** - Basic usage guide
- **TROUBLESHOOTING.md** - Common issues
- **TECHNICAL_SPEC.md** - Detailed specifications
- **ARCHITECTURE.md** - System design

For build-specific issues, check **TROUBLESHOOTING.md** first!
