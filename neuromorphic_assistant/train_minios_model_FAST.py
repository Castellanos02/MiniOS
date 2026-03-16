#!/usr/bin/env python3
"""
FAST training script for neuromorphic_assistant
Optimized for quick training - use this for testing!
"""

import sys
import os
import numpy as np

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_parameters import Model_Params
from assistant import PersonalAssistant

# Activity classes for MiniOS
ACTIVITY_CLASSES = [
    "rest",                    # 0
    "workout",                 # 1
    "creative_work",          # 2
    "study",                  # 3
    "practice_skill",         # 4
    "social_activity",        # 5
    "plan_day",               # 6
    "review_goals",           # 7
    "quick_break",            # 8
    "deep_work",              # 9
    "light_task",             # 10
    "brainstorm",             # 11
    "organize",               # 12
    "learn_something",        # 13
    "physical_activity",      # 14
    "mental_exercise",        # 15
    "relax",                  # 16
    "energize",               # 17
    "focus_session",          # 18
    "free_time",              # 19
]


def create_minios_context(hour, minute, energy, engagement, idle_time, 
                          recent_accepts, recent_rejects):
    """Map MiniOS features to neuromorphic_assistant context format"""
    
    intent = "other"
    dialog_state = "idle"
    
    time_calendar = {
        "hour_of_day": float(hour),
        "is_weekend": 0.0,
        "in_commute": 0.0,
        "busy_now": 1.0 if engagement > 70 else 0.0,
    }
    
    candidate = {
        "suggestion": "none",
        "extra1": float(energy) / 100.0,
        "extra2": float(recent_accepts) / 10.0,
        "extra3": float(recent_rejects) / 10.0,
    }
    
    return {
        "intent": intent,
        "dialog_state": dialog_state,
        "time_calendar": time_calendar,
        "candidate": candidate,
    }


def generate_training_data(num_samples=50):  # REDUCED from 200
    """Generate synthetic training data"""
    
    training_data = []
    
    for _ in range(num_samples):
        hour = np.random.randint(6, 24)
        minute = np.random.randint(0, 60)
        energy = np.random.randint(20, 100)
        engagement = np.random.randint(0, 100)
        idle_time = np.random.rand()
        recent_accepts = np.random.randint(0, 10)
        recent_rejects = np.random.randint(0, 10)
        
        context = create_minios_context(
            hour, minute, energy, engagement, idle_time,
            recent_accepts, recent_rejects
        )
        
        # Determine appropriate activity
        if hour < 9 and energy > 70:
            activity_idx = 1  # workout
        elif 9 <= hour < 12 and energy > 60:
            activity_idx = 9  # deep_work
        elif 12 <= hour < 14:
            activity_idx = 8  # quick_break
        elif 14 <= hour < 17 and engagement > 50:
            activity_idx = 2  # creative_work
        elif 17 <= hour < 20:
            activity_idx = 10  # light_task
        elif hour >= 20:
            activity_idx = 0  # rest
        else:
            activity_idx = 19  # free_time
        
        training_data.append((context, activity_idx))
    
    return training_data


def train_model_fast(num_epochs=10, lr=0.02):  # REDUCED from 30 epochs
    """Train with optimized parameters for speed"""
    
    print("=" * 60)
    print("FAST Training - Neuromorphic Assistant for MiniOS")
    print("=" * 60)
    print("\n⚡ OPTIMIZED FOR SPEED:")
    print("  - Reduced timesteps: 20 (was 50)")
    print("  - Reduced training samples: 50 (was 200)")
    print("  - Reduced epochs: 10 (was 30)")
    print("  - Smaller hidden layer: 16 neurons (was 32)")
    print()
    
    # OPTIMIZED parameters for speed
    params = Model_Params(
        input_size=None,
        hidden_layers=[16],      # REDUCED from 32
        output_size=len(ACTIVITY_CLASSES),
        steps=20,                # REDUCED from 50
    )
    
    assistant = PersonalAssistant(params, class_names=ACTIVITY_CLASSES)
    
    print(f"Model Configuration:")
    print(f"  Hidden neurons: {params.hidden_layers[0]}")
    print(f"  Output classes: {params.output_size}")
    print(f"  Timesteps: {params.steps}")
    
    print(f"\nGenerating {50} training samples...")
    training_data = generate_training_data(50)
    
    print(f"\nTraining for {num_epochs} epochs...")
    print("-" * 60)
    
    import time
    start_time = time.time()
    
    for epoch in range(num_epochs):
        epoch_start = time.time()
        total_loss = 0.0
        correct = 0
        
        for i, (context, true_activity_idx) in enumerate(training_data):
            # Progress indicator
            if i % 10 == 0:
                print(f"  Epoch {epoch+1}/{num_epochs} - Sample {i}/{len(training_data)}...", end='\r')
            
            pred_idx, pred_name, rates = assistant.suggest(context)
            
            if pred_idx == true_activity_idx:
                feedback = "accept"
                correct += 1
            else:
                feedback = "reject"
            
            loss = assistant.update_from_feedback(
                context, pred_idx, feedback, lr=lr
            )
            total_loss += loss
        
        avg_loss = total_loss / len(training_data)
        accuracy = (correct / len(training_data)) * 100
        epoch_time = time.time() - epoch_start
        
        print(f"Epoch {epoch+1:2d}/{num_epochs}: "
              f"Loss = {avg_loss:.4f}, "
              f"Accuracy = {accuracy:5.1f}%, "
              f"Time = {epoch_time:.1f}s")
    
    total_time = time.time() - start_time
    
    print("-" * 60)
    print(f"Training complete in {total_time:.1f}s!")
    print(f"Final accuracy: {accuracy:.1f}%")
    
    return assistant


def save_model(assistant, filepath="minios_activity_model.npz"):
    """Save trained model weights"""
    
    model = assistant.model
    
    np.savez(
        filepath,
        Weight_input_hidden=model.Weight_input_hidden,
        Weight_hidden_output=model.Weight_hidden_output,
        input_size=assistant.params.input_size,
        hidden_size=assistant.params.hidden_layers[0],
        output_size=assistant.params.output_size,
        steps=assistant.params.steps,
        class_names=assistant.class_names,
    )
    
    print(f"\n✓ Model saved to: {filepath}")
    print(f"  Input size: {assistant.params.input_size}")
    print(f"  Hidden size: {assistant.params.hidden_layers[0]}")
    print(f"  Output size: {assistant.params.output_size}")
    print(f"  Total weights: {model.Weight_input_hidden.size + model.Weight_hidden_output.size}")


if __name__ == "__main__":
    print("\n🚀 MiniOS Neuromorphic Assistant - FAST Training\n")
    
    # Fast training
    assistant = train_model_fast(num_epochs=10, lr=0.02)
    
    # Save
    save_model(assistant, "minios_activity_model.npz")
    
    print("\n✓ Ready to export to C!")
    print("  Run: python export_to_minios.py")
    print()
