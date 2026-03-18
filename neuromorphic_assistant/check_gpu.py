#!/usr/bin/env python3
"""
GPU Diagnostic Tool
Check PyTorch and NVML status
"""

import sys

print("="*70)
print("GPU DIAGNOSTIC TOOL")
print("="*70)

# Check PyTorch
print("\n1. Checking PyTorch...")
try:
    import torch
    print(f"   ✓ PyTorch installed: {torch.__version__}")
    
    # Check CUDA
    cuda_available = torch.cuda.is_available()
    print(f"   CUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"   CUDA version: {torch.version.cuda}")
        print(f"   GPU count: {torch.cuda.device_count()}")
        print(f"   GPU name: {torch.cuda.get_device_name(0)}")
        print(f"   ✓ GPU WILL BE USED by snnTorch!")
    else:
        print(f"   ⚠️  CUDA not available - will use CPU")
        print(f"   Install: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        
except ImportError:
    print("   ✗ PyTorch not installed")
    print("   Install: pip install torch snntorch")
    sys.exit(1)

# Check NVML
print("\n2. Checking NVML (for GPU monitoring)...")
try:
    import pynvml
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_name = pynvml.nvmlDeviceGetName(handle)
    if isinstance(gpu_name, bytes):
        gpu_name = gpu_name.decode('utf-8')
    
    print(f"   ✓ NVML working!")
    print(f"   GPU name: {gpu_name}")
    
    # Test power reading
    try:
        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
        print(f"   Current power: {power:.1f} W")
        print(f"   ✓ REAL GPU metrics available!")
    except:
        print(f"   ⚠️  Power reading failed")
        
    pynvml.nvmlShutdown()
    
except Exception as e:
    print(f"   ⚠️  NVML not working: {e}")
    print(f"   GPU will still work via PyTorch!")
    print(f"   Metrics will use estimates (TDP-based)")
    print(f"\n   To fix NVML:")
    print(f"   1. pip uninstall pynvml")
    print(f"   2. pip install nvidia-ml-py3")
    print(f"   3. Ensure NVIDIA drivers are installed")

# Check snnTorch
print("\n3. Checking snnTorch...")
try:
    import snntorch
    print(f"   ✓ snnTorch installed: {snntorch.__version__}")
except ImportError:
    print("   ✗ snnTorch not installed")
    print("   Install: pip install snntorch")
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if torch.cuda.is_available():
    print("\n✅ YOUR SETUP:")
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   PyTorch: ✓ Will use GPU")
    print(f"   snnTorch: ✓ Will train on GPU")
    
    try:
        import pynvml
        pynvml.nvmlInit()
        pynvml.nvmlShutdown()
        print(f"   NVML: ✓ Real power/temp metrics")
    except:
        print(f"   NVML: ⚠️  Estimated metrics (TDP-based)")
        print(f"   Fix: pip install nvidia-ml-py3")
    
    print(f"\n🚀 READY TO TRAIN!")
    print(f"   Run: python train_snntorch_ULTRAFAST.py")
    
else:
    print("\n⚠️  WARNING:")
    print(f"   PyTorch CUDA not available")
    print(f"   Training will use CPU (slower)")
    print(f"\n   To enable GPU:")
    print(f"   1. Install CUDA toolkit from NVIDIA")
    print(f"   2. pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")

print()
