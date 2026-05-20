# MiniOS - Neuromorphic AI Operating System

A custom bootable operating system with integrated Spiking Neural Network (SNN) for proactive activity suggestions.

---

## Project Overview

**MiniOS** is a neuromorphic AI system that uses Spiking Neural Networks (snnTorch) to provide context-aware, proactive activity suggestions in a custom CarPlay-style operating system. The system trains on GPU (NVIDIA/AMD) and deploys the trained model to a bootable OS kernel for real-time CPU inference.

### Key Features

- **Neuromorphic Computing**: Leaky Integrate-and-Fire (LIF) neurons with temporal spike dynamics
- **GPU Training**: Supports both NVIDIA (CUDA) and AMD (DirectML) GPUs
- **Proactive AI**: Automatically suggests activities based on time, energy, and calendar context
- **Bootable OS**: Runs in QEMU/VirtualBox with GRUB multiboot
- **Complete Metrics**: Collects 8 training metrics including power, energy, and inference time


## Quick Start

### Prerequisites

- **Windows 10/11**
- **Python 3.8+**
- **QEMU**
- **Build tools**: GCC, NASM, ld, mkisofs
- **GPU** (optional): NVIDIA or AMD

### Installation

```powershell
# 1. Extract the archive
# (extract minios.tar.gz to your preferred location)

# 2. Install Python dependencies
cd minios\neuromorphic_assistant
pip install torch snntorch numpy psutil

# For NVIDIA GPU:
pip install nvidia-ml-py3

# For AMD GPU:
pip install torch-directml

# 3. Install Linux environment Ubuntu (windows)
wsl --install

# 4. Install build tools (Windows)
sudo apt update
sudo apt uprgade -y
sudo apt install -y build-essential nasm make qemu-system-x86 grub-pc-bin grub-common xorriso
```

---

## Training Workflow

```anaconda prompt
cd minios\neuromorphic_assistant

# Step 1: Start HWiNFO64 logging FIRST
# - Open HWiNFO64
# - Configure → Polling Period → 200ms (recommended)
# - Sensors → Logging → {GPU Type}_recorded_metrics.csv
# - Enable: GPU Power, GPU Temp, GPU Memory

# Step 2: Train
# Train (automatically collects all 8 metrics)
python train_usecase_snn.py --train

# Output: usecase_training_metrics_{GPU Type}.json

# Step 3: Stop HWiNFO64 logging

# Step 4: Combine metrics
python combine_training_metrics.py `
    --training usecase_training_metrics_{GPU Type}.json `
    --hwinfo {GPU Type}_recorded_metrics.csv `
    --output complete_{GPU Type}_metrics.json

# Output: complete_{GPU Type}_metrics.json
# - 8/8 metrics real (all from HWiNFO64)
# - Per-epoch power/temp data

```
---

## Building the OS

### Export Model to Kernel

```anaconda prompt
cd minios\neuromorphic_assistant

# Export trained weights to C header file
python export_usecase_to_minios.py

# Creates: ../kernel/usecase_snn_weights.h
```

### Build Bootable ISO

```Ubuntu
cd minios

# Clean previous builds
make clean

# Build CarPlay OS with neuromorphic AI
make iso-carplay

# Creates: minios_carplay.iso (~2-3 MB)
```

### Run in QEMU

```Ubuntu
# Run the OS
make run-carplay
```

---

## Using the OS

### Navigation

- **Arrow Keys**: Navigate menu
- **Enter**: Select app
- **Q / B**: Back to home

### Calendar App

1. Press **Enter** to open Calendar
2. Press **A** to add AI suggestion
3. Watch neuromorphic SNN suggest activities!

---

## License

This project is for research and educational purposes.

---
