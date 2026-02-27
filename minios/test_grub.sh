#!/bin/bash
# test_grub.sh - Test if GRUB is loading

echo "Testing if GRUB is loading from the ISO..."
echo ""

if [ ! -f "build/minios.iso" ]; then
    echo "❌ ISO not found"
    exit 1
fi

echo "Starting QEMU with serial output to see what's happening..."
echo ""
echo "Watch for:"
echo "  - GRUB messages"
echo "  - Kernel loading messages"
echo "  - Any error messages"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Run with serial output so we can see boot messages
qemu-system-x86_64 \
    -cdrom build/minios.iso \
    -m 128M \
    -boot d \
    -serial stdio \
    -no-reboot

echo ""
echo "QEMU exited"
