#!/bin/bash
# setup_virtualbox.sh - Automated VirtualBox setup for MiniOS

echo "=========================================="
echo "MiniOS VirtualBox Setup"
echo "=========================================="
echo ""

# Check if ISO exists
if [ ! -f "build/minios.iso" ]; then
    echo "❌ ISO not found!"
    echo "Run: make iso"
    exit 1
fi

ISO_PATH="$(realpath build/minios.iso)"
echo "✓ ISO found: $ISO_PATH"
echo ""

# Check if VirtualBox is installed
if ! command -v VBoxManage &> /dev/null; then
    echo "❌ VirtualBox not found!"
    echo ""
    echo "Installation instructions:"
    echo ""
    echo "For WSL (Windows):"
    echo "  1. Download VirtualBox for Windows from:"
    echo "     https://www.virtualbox.org/wiki/Downloads"
    echo "  2. Install on Windows (not in WSL)"
    echo "  3. Add to Windows PATH"
    echo ""
    echo "For Linux:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install virtualbox"
    echo ""
    exit 1
fi

echo "✓ VirtualBox found"
VBoxManage --version
echo ""

# VM Configuration
VM_NAME="MiniOS"

# Check if VM already exists
if VBoxManage list vms | grep -q "\"$VM_NAME\""; then
    echo "⚠ VM '$VM_NAME' already exists"
    echo ""
    read -p "Delete and recreate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing VM..."
        VBoxManage unregistervm "$VM_NAME" --delete 2>/dev/null || true
    else
        echo "Keeping existing VM. To use it, run VirtualBox GUI."
        exit 0
    fi
fi

echo ""
echo "Creating VM: $VM_NAME"
echo "----------------------------------------"

# Create VM
echo "1. Creating virtual machine..."
VBoxManage createvm --name "$VM_NAME" --ostype "Linux_64" --register

# Configure VM
echo "2. Configuring VM settings..."
VBoxManage modifyvm "$VM_NAME" \
    --memory 256 \
    --vram 16 \
    --boot1 dvd \
    --boot2 none \
    --boot3 none \
    --boot4 none \
    --audio none \
    --usb off \
    --graphicscontroller vmsvga

# Create storage controller
echo "3. Adding storage controller..."
VBoxManage storagectl "$VM_NAME" --name "IDE" --add ide

# Attach ISO
echo "4. Attaching ISO..."
VBoxManage storageattach "$VM_NAME" \
    --storagectl "IDE" \
    --port 0 \
    --device 0 \
    --type dvddrive \
    --medium "$ISO_PATH"

echo ""
echo "=========================================="
echo "✓ VM Created Successfully!"
echo "=========================================="
echo ""
echo "VM Name: $VM_NAME"
echo "Memory: 256 MB"
echo "Boot device: DVD (ISO)"
echo ""
echo "To start the VM:"
echo "  VBoxManage startvm \"$VM_NAME\" --type gui"
echo ""
echo "Or use VirtualBox GUI:"
echo "  1. Open VirtualBox"
echo "  2. Select '$VM_NAME'"
echo "  3. Click 'Start'"
echo ""

# Ask if user wants to start now
read -p "Start VM now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting VM..."
    VBoxManage startvm "$VM_NAME" --type gui
else
    echo ""
    echo "VM created but not started."
    echo "Start it anytime with: VBoxManage startvm \"$VM_NAME\" --type gui"
fi
