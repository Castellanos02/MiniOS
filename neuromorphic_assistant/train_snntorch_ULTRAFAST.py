#!/usr/bin/env python3
"""
ULTRA-FAST Neuromorphic SNN Training with snnTorch
5 epochs, 20 samples - completes in ~10-15 seconds with GPU!

Perfect for quick testing and validation
"""

import sys
import os

# Import from main training script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train_snntorch import (
    train_snn, measure_inference_time, save_model,
    add_inference_metrics, GPUMonitor
)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("⚡ ULTRA-FAST NEUROMORPHIC SNN (snnTorch)")
    print("=" * 70)
    print(f"\n⚡ OPTIMIZED FOR SPEED:")
    print(f"  - Epochs: 5 (vs 15 normal)")
    print(f"  - Samples: 20 (vs 100 normal)")
    print(f"  - Hidden neurons: 16 (vs 32 normal)")
    print(f"  - Timesteps: 10 (vs 30 normal)")
    print(f"\n⏱️  Expected time: ~10-15 seconds with GPU!")
    print(f"⚠️  Lower accuracy expected - for testing only!\n")
    
    # Initialize monitor to get device
    monitor = GPUMonitor()
    
    # Train model (fast settings)
    model, monitor = train_snn(
        num_epochs=5,
        num_samples=20,
        hidden_size=16,
        num_steps=10,
        learning_rate=0.01,  # Higher LR for faster convergence
        device=monitor.device
    )
    
    # Save metrics
    monitor.save_metrics('training_metrics.json')
    
    # Measure inference time (fewer tests)
    inference_metrics = measure_inference_time(
        model,
        input_size=10,
        num_steps=10,
        num_tests=50,
        device=monitor.device
    )
    
    # Add to metrics
    add_inference_metrics('training_metrics.json', inference_metrics)
    
    # Save model
    save_model(model, 'minios_snn_model.pth')
    
    # Cleanup
    monitor.cleanup()
    
    print("\n" + "=" * 70)
    print("✓ ULTRA-FAST TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\nFiles created:")
    print(f"  - training_metrics.json (all 8 metrics!)")
    print(f"  - minios_snn_model.pth (trained model)")
    print(f"\n⚠️  Note: Lower accuracy expected (quick test mode)")
    print(f"    For production, use train_snntorch.py")
    print(f"\nNext step: python export_snntorch_to_minios.py")
    print()
