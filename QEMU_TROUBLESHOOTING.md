# QEMU Boot Failure - Advanced Troubleshooting

## Your Situation

You have:
- ✓ ISO exists (`build/minios.iso`)
- ✓ ISO is correct size (5.0M)
- ✓ Built with `make iso`
- ✗ QEMU still shows "could not read the boot disk"

This means the ISO exists but QEMU can't boot from it.

## Step 1: Verify the ISO is Bootable

Run this script:

```bash
./verify_iso.sh
```

This checks:
- Boot signature (0x55AA)
- ISO structure
- Kernel file presence
- GRUB configuration

## Step 2: Try Different QEMU Commands

### Method 1: Standard (what Makefile uses)
```bash
qemu-system-x86_64 -cdrom build/minios.iso -m 128M
```

### Method 2: Explicit boot order
```bash
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -boot d
```

### Method 3: Using -drive
```bash
qemu-system-x86_64 -drive file=build/minios.iso,format=raw,media=cdrom -boot d -m 128M
```

### Method 4: With more debugging
```bash
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -boot d -serial stdio
```

## Step 3: Check QEMU Version

Some QEMU versions have issues:

```bash
qemu-system-x86_64 --version
```

If it's older than 4.0, update:

```bash
sudo apt-get update
sudo apt-get install qemu-system-x86
```

## Step 4: Verify ISO on Your System

### Check file type
```bash
file build/minios.iso
```

Should show one of:
- "ISO 9660 CD-ROM filesystem data"
- "DOS/MBR boot sector"

### Mount and inspect
```bash
mkdir -p /tmp/iso_test
sudo mount -o loop build/minios.iso /tmp/iso_test
ls -la /tmp/iso_test/
ls -la /tmp/iso_test/boot/
sudo umount /tmp/iso_test
```

Should see:
```
/tmp/iso_test/boot/minios.bin
/tmp/iso_test/boot/grub/grub.cfg
```

## Step 5: Rebuild from Scratch

Sometimes the build process gets corrupted:

```bash
# Complete clean
rm -rf build/
make clean

# Rebuild kernel
make iso

# Verify
ls -lh build/minios.iso
file build/minios.iso

# Try to run
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -boot d
```

## Step 6: Check Your Environment

### On macOS
```bash
# Use brew QEMU
brew install qemu
/usr/local/bin/qemu-system-x86_64 -cdrom build/minios.iso -m 128M
```

### On Windows (WSL)
```bash
# Install QEMU in WSL
sudo apt-get install qemu-system-x86

# Make sure X server is running if you want graphics
export DISPLAY=:0
```

### On Linux
```bash
# Make sure you have the right QEMU
which qemu-system-x86_64

# Try with sudo (sometimes permissions matter)
sudo qemu-system-x86_64 -cdrom build/minios.iso -m 128M
```

## Step 7: Try VirtualBox Instead

If QEMU won't work, try VirtualBox:

```bash
# Install VirtualBox
sudo apt-get install virtualbox

# Create VM
VBoxManage createvm --name "MiniOS" --ostype "Linux_64" --register
VBoxManage modifyvm "MiniOS" --memory 128 --boot1 dvd
VBoxManage storagectl "MiniOS" --name "IDE" --add ide
VBoxManage storageattach "MiniOS" --storagectl "IDE" \
    --port 0 --device 0 --type dvddrive --medium $(pwd)/build/minios.iso

# Start VM
VBoxManage startvm "MiniOS"
```

## Common Issues & Solutions

### Issue: "KVM not available"
```bash
# Run without KVM acceleration
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -no-kvm
```

### Issue: "Could not access KVM kernel module"
```bash
# Add yourself to kvm group
sudo usermod -a -G kvm $USER
# Log out and back in
```

### Issue: Display problems
```bash
# Try different graphics
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -vga std
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -vga cirrus
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -nographic
```

### Issue: ISO corrupted
```bash
# Check MD5
md5sum build/minios.iso

# Rebuild
rm -f build/minios.iso
make iso

# Compare MD5
md5sum build/minios.iso
```

## Step 8: Use the Simulators

While debugging the bootable version, use the working simulators:

```bash
# These work perfectly right now!
./minios_gui        # Full GUI with all features
./minios_simulator  # Text interface
```

The simulators have:
- All 20 activities
- Full keyboard support
- Complete ML system
- Logging and export
- No boot issues!

## Diagnostic Commands

Run these and share output if you need help:

```bash
# System info
uname -a
qemu-system-x86_64 --version

# ISO info
ls -lh build/minios.iso
file build/minios.iso
hexdump -C build/minios.iso | head -n 20

# Build info
ls -la build/
ls -la build/isodir/boot/

# QEMU test
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -boot d 2>&1 | tee qemu.log
cat qemu.log
```

## Last Resort: Debug ISO Creation

If nothing works, let's see what grub-mkrescue is doing:

```bash
# Rebuild with verbose output
make clean
rm -rf build/isodir

# Manual ISO creation with debugging
mkdir -p build/isodir/boot/grub
cp build/minios.bin build/isodir/boot/
cp grub.cfg build/isodir/boot/grub/

# Try grub-mkrescue manually
grub-mkrescue -o build/minios_manual.iso build/isodir -v

# Test the manual ISO
qemu-system-x86_64 -cdrom build/minios_manual.iso -m 128M
```

## Success Indicators

When working correctly, you should see:

1. QEMU window opens
2. SeaBIOS message briefly
3. GRUB menu appears:
   ```
   GNU GRUB
   
   MiniOS - Neural Activity Suggester
   MiniOS - Safe Mode
   ```
4. After selecting first option, MiniOS GUI loads

## If Still Not Working

At this point, if nothing works:

1. **Share diagnostic output:**
   ```bash
   ./verify_iso.sh > diagnosis.txt 2>&1
   qemu-system-x86_64 -cdrom build/minios.iso -m 128M -boot d 2>&1 >> diagnosis.txt
   cat diagnosis.txt
   ```

2. **Use the simulators** - they work perfectly!
   ```bash
   ./minios_gui
   ```

3. **Try on different computer** - might be environment-specific issue

4. **Use VirtualBox instead** - more reliable than QEMU sometimes

---

**Quick Tests:**

```bash
# Test 1: Verify ISO
./verify_iso.sh

# Test 2: Try different QEMU command
qemu-system-x86_64 -cdrom build/minios.iso -m 128M -boot d

# Test 3: Use simulators
./minios_gui
```
