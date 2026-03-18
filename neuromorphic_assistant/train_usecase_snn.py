#!/usr/bin/env python3
"""
Train Neuromorphic SNN on Real Use Cases
With default preferences and proactive suggestions

Features:
- Fills idle time proactively (not just reactive)
- Learns from accept/reject feedback
- Context-aware suggestions
- Default preferences that adapt
"""

import torch
import torch.nn as nn
import snntorch as snn
from snntorch import surrogate
from snntorch import functional as SF
import numpy as np
import json
import time
from datetime import datetime

# Import use case data
from use_case_data import (
    generate_use_case_training_data,
    ACTIVITY_LABELS,
    UserProfile,
    USE_CASES
)

# Import GPU monitoring from main training
import sys
sys.path.insert(0, '.')
from train_snntorch import GPUMonitor, NeuromorphicActivitySNN


# ============================================================
# Train with Use Case Data
# ============================================================

def train_use_case_snn(num_samples=500, num_epochs=20, hidden_size=64):
    """Train SNN on real use case scenarios"""
    
    print("\n" + "="*70)
    print("NEUROMORPHIC SNN - USE CASE TRAINING")
    print("="*70)
    print("\nFeatures:")
    print("  ✓ Proactive suggestions (fills idle time)")
    print("  ✓ Default preferences (learns from feedback)")
    print("  ✓ Context-aware (time, energy, calendar)")
    print("  ✓ Realistic use cases from requirements")
    print()
    
    # Initialize GPU monitor
    monitor = GPUMonitor()
    
    # Generate training data
    print(f"Generating {num_samples} use case scenarios...")
    X_train, y_train, scenarios = generate_use_case_training_data(num_samples)
    
    # Convert to tensors
    X_train = torch.tensor(X_train, dtype=torch.float32).to(monitor.device)
    y_train = torch.tensor(y_train, dtype=torch.long).to(monitor.device)
    
    print(f"✓ Generated {len(X_train)} training samples")
    print(f"  Input features: {X_train.shape[1]}")
    print(f"  Activity types: {len(ACTIVITY_LABELS)}")
    
    # Show sample scenarios
    print("\n" + "-"*70)
    print("SAMPLE TRAINING SCENARIOS:")
    print("-"*70)
    for i in range(5):
        s = scenarios[i]
        day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][s['day']]
        print(f"\n{day_name} {s['hour']:02d}:{s['minute']:02d} | "
              f"Energy: {s['energy']}/100 | "
              f"Idle: {s['idle_minutes']}min")
        print(f"  → {s['suggestion']}: {s['reason']}")
    print("-"*70)
    
    # Create model
    input_size = X_train.shape[1]
    output_size = len(ACTIVITY_LABELS)
    
    print(f"\nCreating neuromorphic SNN...")
    print(f"  Input: {input_size} features")
    print(f"  Hidden: {hidden_size} LIF neurons")
    print(f"  Output: {output_size} activity types")
    
    model = NeuromorphicActivitySNN(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        beta=0.9
    ).to(monitor.device)
    
    # Initialize weights
    with torch.no_grad():
        nn.init.xavier_uniform_(model.fc1.weight)
        nn.init.xavier_uniform_(model.fc2.weight)
    
    # Optimizer and loss
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    loss_fn = SF.ce_rate_loss()
    
    # Training
    monitor.start_monitoring()
    
    print(f"\nTraining for {num_epochs} epochs...")
    print("="*70)
    
    best_accuracy = 0
    
    for epoch in range(num_epochs):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        spk_out, mem_out = model(X_train, num_steps=30)
        
        # Loss
        loss = loss_fn(spk_out, y_train)
        
        # Backward
        loss.backward()
        optimizer.step()
        
        # Calculate accuracy
        with torch.no_grad():
            spike_counts = spk_out.sum(0)
            _, predicted = spike_counts.max(1)
            correct = (predicted == y_train).sum().item()
            accuracy = (correct / len(y_train)) * 100
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
        
        # Record metrics
        metrics = monitor.record_metrics(epoch + 1, accuracy, loss.item())
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:2d}/{num_epochs}: "
                  f"Loss={loss.item():.4f}, "
                  f"Acc={accuracy:5.1f}%, "
                  f"Best={best_accuracy:5.1f}%, "
                  f"Time={metrics['time_seconds']:.1f}s")
    
    print("="*70)
    
    # Summary
    summary = monitor.get_summary()
    print(f"\nTraining Summary:")
    print(f"  Total time: {summary['total_time_seconds']:.1f} seconds")
    print(f"  Best accuracy: {best_accuracy:.1f}%")
    print(f"  Final accuracy: {summary['final_accuracy']:.1f}%")
    print(f"  Average power: {summary['average_power_watts']:.1f} W")
    print(f"  Total energy: {summary['total_energy_wh']:.4f} Wh")
    
    return model, monitor, best_accuracy


# ============================================================
# Test Proactive Suggestions
# ============================================================

def test_proactive_suggestions(model, device):
    """Test model on realistic scenarios"""
    
    print("\n" + "="*70)
    print("TESTING PROACTIVE SUGGESTIONS")
    print("="*70)
    
    model.eval()
    
    test_scenarios = [
        {
            'name': 'Monday 7 AM - 30min free before work',
            'features': [7/24, 0, 0/7, 0.8, 0.6, 30/180, 0, 0.5, 0.2, 0],
            'expected': 'workout or morning_activity',
        },
        {
            'name': 'Tuesday 12 PM - 1 hour lunch break',
            'features': [12/24, 0, 1/7, 0.6, 0.5, 60/180, 0, 0.5, 0.2, 0],
            'expected': 'lunch_break or light_activity',
        },
        {
            'name': 'Wednesday 3 PM - 15min idle, low energy',
            'features': [15/24, 0, 2/7, 0.3, 0.4, 15/180, 0, 0.5, 0.2, 0],
            'expected': 'quick_rest or stretch_break',
        },
        {
            'name': 'Friday 6 PM - 2 hours free evening',
            'features': [18/24, 0, 4/7, 0.5, 0.4, 120/180, 0, 0.5, 0.2, 0],
            'expected': 'relax or hobby_time',
        },
        {
            'name': 'Saturday 9 AM - 3 hours free weekend',
            'features': [9/24, 0, 5/7, 0.8, 0.7, 180/180, 0, 0.5, 0.2, 1],
            'expected': 'hobby_time or productive_project',
        },
        {
            'name': 'Monday 9 AM - meeting in 30min',
            'features': [9/24, 0, 0/7, 0.7, 0.8, 0/180, 1, 0.5, 0.2, 0],
            'expected': 'prepare_for_meeting',
        },
    ]
    
    with torch.no_grad():
        for scenario in test_scenarios:
            x = torch.tensor([scenario['features']], dtype=torch.float32).to(device)
            
            # Get prediction
            spk_out, mem_out = model(x, num_steps=30)
            spike_counts = spk_out.sum(0)
            _, predicted = spike_counts.max(1)
            predicted_idx = predicted.item()
            predicted_activity = ACTIVITY_LABELS[predicted_idx]
            
            # Get confidence (spike count)
            confidence = spike_counts[0, predicted_idx].item()
            
            print(f"\n{scenario['name']}")
            print(f"  Expected: {scenario['expected']}")
            print(f"  Suggested: {predicted_activity}")
            print(f"  Confidence: {confidence:.1f} spikes")
    
    print("\n" + "="*70)


# ============================================================
# Save Model with Defaults
# ============================================================

def save_use_case_model(model, best_accuracy, filepath='minios_usecase_model.pth'):
    """Save model with use case metadata"""
    
    # Create default user profile
    default_profile = UserProfile()
    
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_size': model.input_size,
        'hidden_size': model.hidden_size,
        'output_size': model.output_size,
        'activity_labels': ACTIVITY_LABELS,
        'use_cases': USE_CASES,
        'default_preferences': default_profile.preferences,
        'best_accuracy': best_accuracy,
        'proactive': True,
        'fills_idle_time': True,
    }, filepath)
    
    print(f"\n✓ Model saved to: {filepath}")
    print(f"  Includes default preferences")
    print(f"  Includes use case metadata")
    print(f"  Best accuracy: {best_accuracy:.1f}%")


# ============================================================
# Main Training Pipeline
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("USE CASE SNN TRAINING")
    print("Proactive + Learning + Context-Aware")
    print("="*70)
    
    # Train model
    model, monitor, best_accuracy = train_use_case_snn(
        num_samples=500,
        num_epochs=20,
        hidden_size=64
    )
    
    # Save metrics
    monitor.save_metrics('usecase_training_metrics.json')
    
    # Add use case metadata
    with open('usecase_training_metrics.json', 'r') as f:
        data = json.load(f)
    
    data['use_cases'] = {
        'proactive': True,
        'fills_idle_time': True,
        'context_aware': True,
        'learns_preferences': True,
        'num_activities': len(ACTIVITY_LABELS),
        'activities': ACTIVITY_LABELS,
    }
    
    with open('usecase_training_metrics.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Test proactive suggestions
    test_proactive_suggestions(model, monitor.device)
    
    # Measure inference time
    from train_snntorch import measure_inference_time, add_inference_metrics
    
    inference_metrics = measure_inference_time(
        model,
        input_size=10,
        num_steps=30,
        num_tests=100,
        device=monitor.device
    )
    
    add_inference_metrics('usecase_training_metrics.json', inference_metrics)
    
    # Save model
    save_use_case_model(model, best_accuracy)
    
    # Cleanup
    monitor.cleanup()
    
    print("\n" + "="*70)
    print("✓ USE CASE TRAINING COMPLETE!")
    print("="*70)
    print(f"\nFiles created:")
    print(f"  - usecase_training_metrics.json")
    print(f"  - minios_usecase_model.pth")
    print(f"\nModel features:")
    print(f"  ✓ Proactive suggestions")
    print(f"  ✓ Fills idle time automatically")
    print(f"  ✓ Default preferences included")
    print(f"  ✓ Context-aware (time, energy, calendar)")
    print(f"  ✓ Ready for feedback learning")
    print(f"\nNext: python export_usecase_to_minios.py")
    print()
