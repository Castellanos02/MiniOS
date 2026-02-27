#!/bin/bash
# test_qemu.sh - Test QEMU directly with different options

echo "======================================"
echo "Testing QEMU Boot Methods"
echo "======================================"
echo ""

# Check ISO exists
if [ ! -f "build/minios.iso" ]; then
    echo "❌ ISO not found!"
    echo "Run: make iso"
    exit 1
fi

echo "✓ ISO found: build/minios.iso"
ls -lh build/minios.iso
echo ""

# Test 1: Standard cdrom boot
echo "Test 1: Booting with -cdrom (standard method)"
echo "Command: qemu-system-x86_64 -cdrom build/minios.iso -m 128M"
echo ""
echo "Starting in 3 seconds... (Ctrl+C to cancel)"
sleep 3

qemu-system-x86_64 -cdrom build/minios.iso -m 128M

# If that didn't work, try alternative
echo ""
echo "======================================"
echo "Did that work? If not, trying alternative..."
echo "======================================"
sleep 2

# Test 2: Drive with explicit boot
echo ""
echo "Test 2: Using -drive with explicit boot order"
echo "Command: qemu-system-x86_64 -drive file=build/minios.iso,format=raw,media=cdrom -boot d -m 128M"
echo ""
sleep 2

qemu-system-x86_64 -drive file=build/minios.iso,format=raw,media=cdrom -boot d -m 128M
