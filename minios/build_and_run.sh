#!/bin/bash
# build_and_run.sh - Build and run MiniOS in QEMU

set -e  # Exit on error

echo "======================================"
echo "MiniOS Build and Run Script"
echo "======================================"
echo ""

# Check for required tools
echo "Checking for required tools..."

if ! command -v nasm &> /dev/null; then
    echo "❌ NASM not found. Install with:"
    echo "   sudo apt-get install nasm"
    exit 1
fi

if ! command -v grub-mkrescue &> /dev/null; then
    echo "❌ grub-mkrescue not found. Install with:"
    echo "   sudo apt-get install grub-pc-bin xorriso mtools"
    exit 1
fi

if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo "❌ QEMU not found. Install with:"
    echo "   sudo apt-get install qemu-system-x86"
    exit 1
fi

echo "✓ All tools found"
echo ""

# Clean previous build
echo "Cleaning previous build..."
make clean

# Build ISO
echo ""
echo "Building bootable ISO with GUI..."
make iso

# Check if ISO was created
if [ ! -f "build/minios.iso" ]; then
    echo "❌ Error: ISO file not created"
    exit 1
fi

echo ""
echo "✓ ISO created: build/minios.iso"
ls -lh build/minios.iso

# Run in QEMU
echo ""
echo "======================================"
echo "Starting QEMU..."
echo "======================================"
echo ""
echo "Controls:"
echo "  A - Accept activity (green notification)"
echo "  R - Reject activity (red notification)"
echo "  N - Next activity"
echo ""
echo "Press Ctrl+Alt+G to release mouse/keyboard from QEMU"
echo ""

make run-iso
