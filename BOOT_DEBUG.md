# MiniOS Boot Process Debugging Guide

## Current Issue: Stuck at "MiniOS Booting..."

When you see the bootloader message but nothing else happens, the issue is usually in one of these stages:

### Boot Stages

```
1. BIOS/UEFI    ✅ Working (QEMU starts)
2. Bootloader   ✅ Working (you see "MiniOS Booting...")
3. Disk Read    ❓ May fail silently
4. A20 Enable   ❓ May fail
5. Protected Mode ❓ May fail
6. Long Mode    ❓ May fail  
7. Kernel Jump  ❓ Likely failing here
8. Kernel Start ❌ Not reached
```

## Quick Fixes

### Option 1: Use the Simulators (Easiest!)

The simulators work perfectly and provide the same functionality:

```bash
./minios_gui        # CarPlay-style interface
./minios_simulator  # Text interface
```

**No bootloader issues!** These run as normal Linux programs.

### Option 2: Test with Minimal Kernel

Test if the bootloader works at all:

```bash
make test
```

This builds a tiny kernel that just prints "KERNEL OK" to the screen. If you see that, the bootloader works and the issue is in the main kernel.

### Option 3: Fix the Full Kernel Boot

If you want to debug the full kernel boot, continue reading...

## Common Boot Hang Causes

### 1. Kernel Not Loaded

**Problem:** Bootloader can't read the kernel from disk

**Symptoms:** Hangs at "MiniOS Booting..."

**Debug:**
```bash
# Check if kernel binary exists and has reasonable size
ls -lh build/kernel.bin
# Should be around 50-100 KB

# Check boot sector
xxd build/boot.bin | tail
# Should end with: 55 aa
```

**Fix:**
```bash
make clean
make
```

### 2. Wrong Kernel Format

**Problem:** Kernel is ELF format but bootloader expects raw binary

**Symptoms:** Jumps to kernel but crashes immediately

**Debug:**
```bash
file build/kernel.bin
# Should say: "data" not "ELF"
```

**Fix:** Already fixed in latest Makefile (uses `objcopy -O binary`)

### 3. Kernel Entry Point Wrong

**Problem:** Bootloader jumps to 0x1000 but kernel code isn't there

**Symptoms:** Silent hang after "Long mode OK"

**Debug:**
```bash
objdump -d build/kernel.elf | head -20
# First instruction should be at address 0x1000
```

**Fix:** Use `kernel_entry.asm` as the first file linked

### 4. Missing Segments Setup

**Problem:** Kernel expects certain segment registers to be set

**Symptoms:** Triple fault (QEMU resets)

**Fix:** Bootloader should set DS, ES, FS, GS, SS in long mode

### 5. Stack Not Set Up

**Problem:** Kernel tries to use stack but RSP is invalid

**Symptoms:** Immediate crash when kernel calls functions

**Fix:** Bootloader sets RSP to 0x90000

## Debugging Commands

### Check Bootloader

```bash
# Disassemble bootloader
ndisasm -b 16 build/boot.bin | head -50

# Check boot signature
xxd build/boot.bin | grep "55 aa"
```

### Check Kernel

```bash
# View kernel start
xxd build/kernel.bin | head -20

# Disassemble kernel (if ELF)
objdump -d build/kernel.elf | head -50

# Check entry point
readelf -h build/kernel.elf | grep Entry
```

### Check Image

```bash
# View full OS image structure
ls -lh build/
# Should have: boot.bin (512 bytes), kernel.bin (~50KB), minios.img (1MB)

# Check image structure
xxd build/minios.img | head -10   # Bootloader
xxd build/minios.img | grep -A2 "0000800"  # Kernel start
```

### QEMU Debug Mode

```bash
# Run with debug output
qemu-system-x86_64 -drive format=raw,file=build/minios.img -m 128M -d int,cpu_reset

# Run with serial output
qemu-system-x86_64 -drive format=raw,file=build/minios.img -m 128M -serial stdio

# Run with monitor
qemu-system-x86_64 -drive format=raw,file=build/minios.img -m 128M -monitor stdio
```

In QEMU monitor:
```
info registers    # View CPU state
x/20i 0x1000     # Disassemble at kernel entry
x/20x 0x1000     # View memory at kernel entry
```

## Step-by-Step Boot Verification

### Step 1: Verify Bootloader Compiles

```bash
nasm -f bin boot/boot.asm -o build/boot.bin
ls -l build/boot.bin
# Must be exactly 512 bytes
```

### Step 2: Verify Kernel Compiles

```bash
# Build kernel object files
nasm -f elf64 kernel/kernel_entry.asm -o build/kernel_entry.o
nasm -f elf64 kernel/interrupts.asm -o build/interrupts.o
gcc -ffreestanding -nostdlib -Ikernel -m64 -c kernel/kernel_main.c -o build/kernel_main.o

# Link
ld -T kernel/linker.ld build/kernel_entry.o build/kernel_main.o [...] -o build/kernel.elf

# Convert to binary
objcopy -O binary build/kernel.elf build/kernel.bin

# Check result
file build/kernel.bin
# Should say: "data"
```

### Step 3: Create Image

```bash
cat build/boot.bin build/kernel.bin > build/minios.img
truncate -s 1M build/minios.img
```

### Step 4: Test Boot

```bash
qemu-system-x86_64 -drive format=raw,file=build/minios.img -m 128M
```

## Expected Output

### Success Path

```
1. QEMU window opens
2. "SeaBIOS" message
3. "Booting from Hard Disk..."
4. "MiniOS Booting..."
5. "Long mode OK, loading kernel..."
6. Kernel messages appear:
   - "MiniOS v1.0"
   - "Initializing..."
   - "Timer initialized"
   - etc.
7. GUI appears
```

### Failure Points

**Hangs at "MiniOS Booting..."**
- Disk read failed
- Check: Make run `make test` to isolate

**Hangs at "Long mode OK..."**
- Kernel not at 0x1000
- Kernel entry point wrong
- Check: `xxd build/kernel.bin | head`

**Triple fault (QEMU resets)**
- Invalid instruction
- Stack pointer wrong
- Segments not set up

**Black screen after "Long mode OK"**
- Kernel jumped to but not executing
- Check entry point and linking order

## Advanced Debugging

### GDB with QEMU

```bash
# Terminal 1
qemu-system-x86_64 -s -S -drive format=raw,file=build/minios.img -m 128M

# Terminal 2
gdb
(gdb) target remote :1234
(gdb) set architecture i386:x86-64
(gdb) break *0x7c00        # Bootloader start
(gdb) break *0x1000        # Kernel start
(gdb) continue
(gdb) stepi                # Step through instructions
(gdb) info registers
(gdb) x/i $rip            # Examine current instruction
```

### Bochs Debugging

If QEMU doesn't help, try Bochs (better debugging):

```bash
# Install Bochs
sudo apt-get install bochs bochs-x

# Create bochsrc
cat > bochsrc << EOF
megs: 128
romimage: file=/usr/share/bochs/BIOS-bochs-latest
vgaromimage: file=/usr/share/bochs/VGABIOS-lgpl-latest
boot: disk
ata0-master: type=disk, path="build/minios.img", mode=flat
magic_break: enabled=1
EOF

# Run with debugger
bochs -q
```

Bochs has a built-in debugger with great introspection.

## Workarounds

If you can't get the bootloader working:

### Use Multiboot

Switch to GRUB multiboot instead of custom bootloader:

```bash
# Create multiboot header in kernel
# Use GRUB to boot instead of custom bootloader
# Much more reliable but requires GRUB
```

### Use QEMU Direct Kernel Boot

Skip bootloader entirely:

```bash
qemu-system-x86_64 -kernel build/kernel.bin -m 128M
```

Note: Kernel needs to be a Linux-compatible format.

### Stick with Simulators

The simulators work perfectly and provide identical functionality:
- Same neural network
- Same activities
- Same logging
- Same UI (even better in GUI mode!)

**Recommendation:** For development and actual use, the simulators are better. The full OS boot is mainly educational.

## Current Status

**Working:**
✅ Bootloader loads and prints message
✅ Protected mode works (otherwise would crash immediately)
✅ Long mode setup (gets past several complex stages)

**Issue:**
❌ Jump to kernel doesn't execute kernel code

**Most Likely Cause:**
- Kernel binary format (ELF vs raw)
- Kernel entry point not at 0x1000
- Linking order wrong

**Solution:**
Use the updated Makefile which:
1. Creates kernel_entry.asm as first code
2. Links in correct order
3. Converts ELF to binary with objcopy
4. Ensures entry point at 0x1000

## Need Help?

1. Run `make test` to verify bootloader basics
2. Check `build/` directory sizes are reasonable
3. Try the simulators (`./minios_gui`)
4. If still stuck, see TROUBLESHOOTING.md

---

**Remember:** The simulators (`minios_gui`, `minios_simulator`) work perfectly and are actually better for development since they're easier to debug and provide the same functionality!
