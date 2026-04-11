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

### Performance

- **Training Accuracy**: 89-91%
- **Training Time**: 9-12 seconds (GPU)
- **Inference Latency**: 24ms average
- **Energy Consumption**: 0.027 Wh
- **Activities**: 20 context-aware suggestions

---

## Quick Start

### Prerequisites

- **Windows 10/11** (for AMD GPU support with DirectML)
- **Python 3.8+**
- **QEMU** or **VirtualBox**
- **Build tools**: GCC, NASM, ld, mkisofs
- **GPU** (optional but recommended): NVIDIA or AMD

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

# 3. Install build tools (Windows)
choco install make nasm qemu
# Or use WSL for easier builds
```

---

## Training Workflow

### Option A: NVIDIA GPU (Simple - 1 Step)

```powershell
cd minios\neuromorphic_assistant

# Train (automatically collects all 8 metrics)
python train_usecase_snn.py

# Output: usecase_training_metrics.json
# - 6/8 metrics real (power/energy estimated)
# - Training complete in ~10 seconds
```

### Option B: AMD GPU (2 Steps - Real Power Data)

```powershell
cd minios\neuromorphic_assistant

# Step 1: Start HWiNFO64 logging FIRST
# - Open HWiNFO64
# - Configure → Polling Period → 200ms (recommended)
# - Sensors → Logging → training_amd_snntorch.csv
# - Enable: GPU Power, GPU Temp, GPU Memory

# Step 2: Train
python train_usecase_snn.py

# Step 3: Stop HWiNFO64 logging

# Step 4: Combine metrics
python combine_training_metrics.py `
    --training usecase_training_metrics.json `
    --hwinfo training_amd_snntorch.csv `
    --output complete_amd_metrics.json

# Output: complete_amd_metrics.json
# - 8/8 metrics real (all from HWiNFO64)
# - Per-epoch power/temp data
```

---

## Building the OS

### Export Model to Kernel

```powershell
cd minios\neuromorphic_assistant

# Export trained weights to C header file
python export_usecase_to_minios.py

# Creates: ../kernel/usecase_snn_weights.h
```

### Build Bootable ISO

```powershell
cd minios

# Clean previous builds
make clean

# Build CarPlay OS with neuromorphic AI
make iso-carplay

# Creates: minios_carplay.iso (~2-3 MB)
```

### Run in QEMU

```powershell
# Run the OS
make run-carplay

# Or manually:
qemu-system-i386 -cdrom minios_carplay.iso -m 128M
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

### Proactive Behavior

The system automatically checks every 30 minutes (at :00 and :30) for idle calendar time:
- If ≥30 minutes free → adds AI suggestion
- Context-aware: considers time, energy, day of week
- Anti-repetition: tracks last 3 suggestions for variety

---

## Metrics Collected

### All 8 Required Metrics

| # | Metric | Source | NVIDIA | AMD |
|---|--------|--------|--------|-----|
| 1 | **Accuracy** | Training loop | Real | Real |
| 2 | **RAM** | psutil | Real | Real |
| 3 | **GPU Allocated** | PyTorch CUDA | Real | Real (HWiNFO64) |
| 4 | **GPU Reserved** | PyTorch CUDA | Real | Real (HWiNFO64) |
| 5 | **Power** | NVML / HWiNFO64 | Est. | Real (HWiNFO64) |
| 6 | **Energy** | Calculated | Est. | Real (HWiNFO64) |
| 7 | **Time** | time.time() | Real | Real |
| 8 | **Inference** | 100 tests | Real | Real |

**NVIDIA**: 6/8 real, 2/8 estimated (power uses 115W TDP)  
**AMD**: 8/8 real (with HWiNFO64)

---

## Project Structure

```
minios/
├── kernel/
│   ├── kernel_carplay.c          # Main OS kernel with AI integration
│   ├── usecase_snn_weights.h     # Exported SNN weights (generated)
│   ├── multiboot_header.asm      # GRUB multiboot header
│   ├── kernel_entry.asm          # Kernel entry point
│   └── linker_multiboot.ld       # Linker script
├── neuromorphic_assistant/
│   ├── train_usecase_snn.py      # Main training script (GPU)
│   ├── export_usecase_to_minios.py  # Export model to C
│   ├── combine_training_metrics.py  # Combine with HWiNFO64
│   ├── use_case_data.py          # Training data generator
│   └── check_gpu.py              # GPU diagnostics
├── Makefile                      # Build system
└── README.md                     # This file
```

---

## Neuromorphic Architecture

### Network Structure

```
Input Layer:   10 features (hour, minute, day, energy, engagement, etc.)
Hidden Layer:  64 LIF neurons (beta=0.9, membrane dynamics)
Output Layer:  20 LIF neurons (activity types)
Timesteps:     20 (spike-based temporal processing)
```

### Activities (20 Types)

**Idle Time Filling (0-11)**:
- quick_rest, stretch_break, quick_task, workout, lunch_break
- creative_work, light_activity, deep_work, productive_project
- relax, hobby_time, flexible_activity

**Meeting Context (12-14)**:
- prepare_for_meeting, review_notes, stay_ready

**General (15-19)**:
- check_in, music_suggestion, podcast_suggestion
- route_suggestion, social_suggestion

### Learning Algorithm

- **Framework**: snnTorch (PyTorch-based)
- **Neuron Model**: Leaky Integrate-and-Fire (LIF)
- **Training**: Surrogate gradient descent
- **Loss**: Spike count cross-entropy
- **Optimizer**: Adam (lr=0.001)

---

## Troubleshooting

### GPU Not Detected (AMD)

```powershell
# Install DirectML support
pip install torch-directml

# Verify
python -c "import torch_directml; print(torch_directml.is_available())"
```

### Build Errors

```powershell
# Use WSL for easier builds
wsl
cd /mnt/c/path/to/minios
sudo apt install build-essential nasm genisoimage qemu-system-x86
make clean && make iso-carplay
```

### QEMU Not Found

```powershell
# Install QEMU
choco install qemu

# Or download from: https://www.qemu.org/download/
```

### HWiNFO64 Missing Sensors

1. Make sure GPU sensors are enabled in HWiNFO64
2. Set polling to 200ms (Configure → Polling Period → 200)
3. Check for "GPU Power [W]" and "GPU Temperature [°C]"

---

## Technical Details

### Training Hyperparameters

```python
num_epochs = 20
batch_size = 1 (online learning)
hidden_size = 64
num_timesteps = 20
beta = 0.9 (membrane leak)
learning_rate = 0.001
```

### Inference Process

1. Extract 10 context features from current state
2. Forward pass through 64 LIF neurons (hidden layer)
3. Spike accumulation over 20 timesteps
4. Winner-take-all: activity with most output spikes
5. Return suggestion in 20-25ms

### OS Integration

1. Train SNN on GPU → PyTorch model (.pth)
2. Export weights → C header file (.h)
3. Compile into kernel → Bootable ISO (.iso)
4. Run inference on CPU → Real-time suggestions

---

## Academic Description

This project implements a neuromorphic Spiking Neural Network (SNN) using Leaky Integrate-and-Fire neurons for proactive activity suggestion in a custom operating system. The system trains on GPU (NVIDIA/AMD) using snnTorch, achieving 89-91% accuracy on context-aware recommendations, then deploys the model weights to a bootable OS kernel for real-time CPU inference. The neuromorphic architecture demonstrates energy-efficient edge computing through spike-based temporal processing, collecting comprehensive metrics including power consumption (0.026 Wh), inference latency (8-24ms), and learning dynamics across both training and deployment phases.

---

## License

This project is for research and educational purposes.

---
