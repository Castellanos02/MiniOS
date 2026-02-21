#!/bin/bash
# direct_run.sh - Run QEMU directly without using Makefile

echo "======================================"
echo "Direct QEMU Test"
echo "======================================"
echo ""

# Get absolute path
ISO_PATH="$(pwd)/build/minios.iso"

echo "Looking for ISO at: $ISO_PATH"

if [ ! -f "$ISO_PATH" ]; then
    echo "❌ ISO not found at: $ISO_PATH"
    echo ""
    echo "Current directory: $(pwd)"
    echo "Files in build/:"
    ls -la build/
    exit 1
fi

echo "✓ Found ISO"
ls -lh "$ISO_PATH"
echo ""

echo "File type:"
file "$ISO_PATH"
echo ""

echo "Starting QEMU with absolute path..."
echo "Command: qemu-system-x86_64 -cdrom \"$ISO_PATH\" -m 128M -boot d"
echo ""

# Use absolute path to avoid any confusion
exec qemu-system-x86_64 -cdrom "$ISO_PATH" -m 128M -boot d
