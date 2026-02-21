# STEP-BY-STEP: Fix "Could Not Read Boot Disk" Error

## What's Happening

QEMU is trying to boot from the ISO, but the ISO file either:
1. Doesn't exist (most common)
2. Wasn't built correctly
3. Is corrupted

## The Solution - Follow These Exact Steps

### Step 1: Check Current Status

```bash
cd minios
./diagnose.sh
```

This will tell you exactly what's missing.

### Step 2: Build the ISO (THE CRITICAL STEP)

```bash
make iso
```

**Wait for it to complete!** This takes 10-30 seconds.

You should see output like:
```
Building multiboot kernel with GUI...
✓ Built: build/minios.bin
Creating GRUB ISO...
✓ Created: build/minios.iso
```

### Step 3: Verify ISO Was Created

```bash
ls -lh build/minios.iso
```

You should see something like:
```
-rw-r--r-- 1 user user 4.2M Feb 20 12:34 build/minios.iso
```

If you don't see this file, the build failed. Go to "Troubleshooting" below.

### Step 4: Run QEMU

```bash
make run-iso
```

QEMU should now boot successfully!

## Still Getting the Error?

### If `make iso` Failed

**Check for errors in the output:**

```bash
make iso 2>&1 | tee build.log
cat build.log
```

Common errors:

**Error: "grub-mkrescue: command not found"**
```bash
sudo apt-get install grub-pc-bin xorriso mtools
```

**Error: "nasm: command not found"**
```bash
sudo apt-get install nasm
```

**Error: "No space left on device"**
```bash
df -h    # Check disk space
# Clean up if needed
```

### If ISO Exists But QEMU Still Fails

**Verify the ISO is valid:**

```bash
file build/minios.iso
```

Should show:
```
build/minios.iso: ISO 9660 CD-ROM filesystem data
```

Or:
```
build/minios.iso: DOS/MBR boot sector
```

**If it shows something else**, rebuild:

```bash
rm -f build/minios.iso
make iso
```

### If Everything Looks Good But Still Fails

Try running QEMU manually with verbose output:

```bash
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -boot d
```

The `-boot d` explicitly tells QEMU to boot from CD-ROM.

## Complete Clean Build

If nothing else works, do a completely clean build:

```bash
# 1. Remove everything
rm -rf build/
make clean

# 2. Create fresh build directory
mkdir -p build

# 3. Build ISO from scratch
make iso

# 4. Verify it was created
ls -lh build/minios.iso

# 5. Run
make run-iso
```

## Using the Automated Script

The easiest way is to use the build script:

```bash
./build_and_run.sh
```

This handles everything automatically and shows clear error messages.

## What Each File Should Be

After a successful build:

```
build/
├── minios.iso              # ~4-5 MB, bootable ISO
├── minios.bin              # ~50-100 KB, kernel binary
├── isodir/                 # ISO directory structure
│   └── boot/
│       ├── minios.bin      # Kernel (copy)
│       └── grub/
│           ├── grub.cfg    # GRUB menu
│           └── i386-pc/    # GRUB bootloader files
├── kernel_full.o           # Compiled kernel
└── multiboot_header.o      # Compiled multiboot header
```

## Test Checklist

Run these commands in order and check each result:

```bash
# 1. Check tools
which nasm grub-mkrescue qemu-system-x86_64
# All three should show paths

# 2. Build ISO
make iso
# Should end with "✓ Created: build/minios.iso"

# 3. Verify ISO
ls -lh build/minios.iso
# Should show file of ~4-5 MB

# 4. Check ISO type
file build/minios.iso
# Should mention "ISO" or "boot sector"

# 5. Run
make run-iso
# QEMU should start and show GRUB menu
```

## Alternative: Use Simulators

If you can't get the bootable version working, the simulators work perfectly:

```bash
# CarPlay-style GUI
./minios_gui

# Text interface
./minios_simulator
```

These don't need any building and have all features working!

## Understanding the Error

The error "Booting from DVD/CD... Boot failed: could not read the boot disk" means:

1. **QEMU starts** ✓
2. **SeaBIOS loads** ✓
3. **QEMU tries to boot from CD** ✓
4. **Can't find/read the ISO** ✗

This happens when:
- ISO file doesn't exist (`build/minios.iso` missing)
- ISO file is empty or corrupted
- QEMU can't access the file (permissions?)
- Wrong path in Makefile

## Quick Debug Commands

```bash
# Does ISO exist?
test -f build/minios.iso && echo "YES" || echo "NO"

# What size?
du -h build/minios.iso

# Can you read it?
file build/minios.iso

# What's in build/?
ls -la build/

# Try running manually
qemu-system-x86_64 -cdrom build/minios.iso -m 128M
```

## The Working Command Sequence

This sequence ALWAYS works if tools are installed:

```bash
cd minios
rm -rf build/              # Remove old build
make iso                   # Build new ISO (wait for completion!)
ls -lh build/minios.iso   # Verify ISO exists
make run-iso              # Run in QEMU
```

## Summary

**The fix is simple:**

1. Run `make iso` (and wait for it to finish!)
2. Verify `build/minios.iso` exists
3. Run `make run-iso`

**Or just use the script:**

```bash
./build_and_run.sh
```

---

**If you're still stuck after following this guide, run `./diagnose.sh` and share the output.**
