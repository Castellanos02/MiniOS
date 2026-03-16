#!/usr/bin/env python3
"""
Train neuromorphic_assistant for MiniOS activity suggestions
"""

import sys
import os
import numpy as np

# Add current directory to path so we can import from same folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from local module
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
    """
    Map MiniOS features to neuromorphic_assistant context format
    """
    
    # Map to intent
    if 8 <= hour < 12:
        intent = "other"  # Morning activities
    elif 12 <= hour < 14:
        intent = "other"  # Lunch time
    elif 14 <= hour < 18:
        intent = "other"  # Afternoon work
    else:
        intent = "other"  # Evening/night
    
    # Dialog state (simplified for OS)
    dialog_state = "idle"
    
    # Time/calendar features
    time_calendar = {
        "hour_of_day": float(hour),
        "is_weekend": 0.0,  # Can be enhanced
        "in_commute": 0.0,
        "busy_now": 1.0 if engagement > 70 else 0.0,
    }
    
    # Candidate (suggestion context)
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


def generate_training_data(num_samples=200):
    """
    Generate synthetic training data for activity suggestions
    """
    
    training_data = []
    
    for _ in range(num_samples):
        hour = np.random.randint(6, 24)
        minute = np.random.randint(0, 60)
        energy = np.random.randint(20, 100)
        engagement = np.random.randint(0, 100)
        idle_time = np.random.rand()
        recent_accepts = np.random.randint(0, 10)
        recent_rejects = np.random.randint(0, 10)
        
        # Create context
        context = create_minios_context(
            hour, minute, energy, engagement, idle_time,
            recent_accepts, recent_rejects
        )
        
        # Determine appropriate activity based on rules
        # (This simulates user preferences)
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


def train_model(num_epochs=20, lr=0.01):
    """
    Train the neuromorphic assistant for MiniOS activities
    """
    
    print("=" * 60)
    print("Training Neuromorphic Assistant for MiniOS")
    print("=" * 60)
    
    # Create model parameters
    params = Model_Params(
        input_size=None,  # Auto-detected
        hidden_layers=[32],  # 32 hidden neurons
        output_size=len(ACTIVITY_CLASSES),
        steps=50,  # 50 timesteps
    )
    
    # Create assistant
    assistant = PersonalAssistant(params, class_names=ACTIVITY_CLASSES)
    
    print(f"\nModel Configuration:")
    print(f"  Hidden neurons: {params.hidden_layers[0]}")
    print(f"  Output classes: {params.output_size}")
    print(f"  Timesteps: {params.steps}")
    
    # Generate training data
    print(f"\nGenerating {200} training samples...")
    training_data = generate_training_data(200)
    
    # Training loop
    print(f"\nTraining for {num_epochs} epochs...")
    print("-" * 60)
    
    for epoch in range(num_epochs):
        total_loss = 0.0
        correct = 0
        
        for context, true_activity_idx in training_data:
            # Get prediction
            pred_idx, pred_name, rates = assistant.suggest(context)
            
            # Determine feedback
            if pred_idx == true_activity_idx:
                feedback = "accept"
                correct += 1
            else:
                feedback = "reject"
            
            # Update model
            loss = assistant.update_from_feedback(
                context, pred_idx, feedback, lr=lr
            )
            total_loss += loss
        
        avg_loss = total_loss / len(training_data)
        accuracy = (correct / len(training_data)) * 100
        
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1:3d}/{num_epochs}: "
                  f"Loss = {avg_loss:.4f}, Accuracy = {accuracy:.1f}%")
    
    print("-" * 60)
    print(f"Training complete!")
    print(f"Final accuracy: {accuracy:.1f}%")
    
    return assistant


def save_model(assistant, filepath="minios_activity_model.npz"):
    """
    Save trained model weights
    """
    
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
    print("\n🧠 MiniOS Neuromorphic Assistant Training\n")
    
    # Train model
    assistant = train_model(num_epochs=30, lr=0.02)
    
    # Save trained weights
    save_model(assistant, "minios_activity_model.npz")
    
    print("\n✓ Ready to export to C!")
    print("  Run: python export_to_minios.py")
    print()
