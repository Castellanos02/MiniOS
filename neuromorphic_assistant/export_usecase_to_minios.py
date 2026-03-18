#!/usr/bin/env python3
"""
Export Use Case Model to MiniOS C Code
Includes default preferences and proactive suggestion logic
"""

import torch
import numpy as np
import json


def load_usecase_model(model_path='minios_usecase_model.pth'):
    """Load trained use case model"""
    
    print(f"\n{'='*70}")
    print(f"LOADING USE CASE MODEL")
    print(f"{'='*70}")
    
    checkpoint = torch.load(model_path, map_location='cpu')
    
    print(f"✓ Model loaded from: {model_path}")
    print(f"  Input size: {checkpoint['input_size']}")
    print(f"  Hidden size: {checkpoint['hidden_size']}")
    print(f"  Output size: {checkpoint['output_size']}")
    print(f"  Activities: {len(checkpoint['activity_labels'])}")
    print(f"  Proactive: {checkpoint.get('proactive', False)}")
    print(f"  Fills idle time: {checkpoint.get('fills_idle_time', False)}")
    
    return checkpoint


def extract_weights(checkpoint):
    """Extract weights from PyTorch model"""
    
    state_dict = checkpoint['model_state_dict']
    
    W_input_hidden = state_dict['fc1.weight'].numpy()
    b_input_hidden = state_dict['fc1.bias'].numpy()
    
    W_hidden_output = state_dict['fc2.weight'].numpy()
    b_hidden_output = state_dict['fc2.bias'].numpy()
    
    print(f"\n✓ Weights extracted:")
    print(f"  Input->Hidden: {W_input_hidden.shape}")
    print(f"  Hidden->Output: {W_hidden_output.shape}")
    
    return {
        'W_input_hidden': W_input_hidden,
        'b_input_hidden': b_input_hidden,
        'W_hidden_output': W_hidden_output,
        'b_hidden_output': b_hidden_output,
    }


def generate_c_header(checkpoint, weights, output_path='../kernel/usecase_snn_weights.h'):
    """Generate C header with weights and defaults"""
    
    print(f"\n{'='*70}")
    print(f"GENERATING C HEADER FILE")
    print(f"{'='*70}")
    
    input_size = checkpoint['input_size']
    hidden_size = checkpoint['hidden_size']
    output_size = checkpoint['output_size']
    activity_labels = checkpoint['activity_labels']
    default_prefs = checkpoint.get('default_preferences', {})
    
    W_ih = weights['W_input_hidden']
    b_ih = weights['b_input_hidden']
    W_ho = weights['W_hidden_output']
    b_ho = weights['b_hidden_output']
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"""/*
 * Use Case Neuromorphic SNN - Exported Weights
 * 
 * Features:
 * - Proactive suggestions (fills idle time)
 * - Default preferences (adapts to user)
 * - Context-aware (time, energy, calendar)
 * - Learning from feedback (accept/reject)
 * 
 * Architecture:
 * - Input: {input_size} context features
 * - Hidden: {hidden_size} LIF neurons
 * - Output: {output_size} activity types
 */

#ifndef USECASE_SNN_WEIGHTS_H
#define USECASE_SNN_WEIGHTS_H

#define UC_INPUT_SIZE {input_size}
#define UC_HIDDEN_SIZE {hidden_size}
#define UC_OUTPUT_SIZE {output_size}
#define UC_NUM_STEPS 20  // Timesteps for inference

// Activity labels
static const char* ACTIVITY_NAMES[UC_OUTPUT_SIZE] = {{
""")
        
        # Write activity names
        for i, name in enumerate(activity_labels):
            f.write(f'    "{name}"')
            if i < len(activity_labels) - 1:
                f.write(',\n')
            else:
                f.write('\n')
        f.write('};\n\n')
        
        # Write default preferences
        f.write('// Default user preferences\n')
        f.write('typedef struct {\n')
        f.write('    const char* music_genre;\n')
        f.write('    const char* route_preference;\n')
        f.write('    const char* gas_preference;\n')
        f.write('    const char* morning_routine;\n')
        f.write('    const char* break_activity;\n')
        f.write('    const char* evening_activity;\n')
        f.write('    int podcast_continue;\n')
        f.write('    const char* parking_spot;\n')
        f.write('} UserPreferences;\n\n')
        
        f.write('static const UserPreferences DEFAULT_PREFS = {\n')
        f.write(f'    .music_genre = "{default_prefs.get("music_genre", "90s_road_trip")}",\n')
        f.write(f'    .route_preference = "{default_prefs.get("route_preference", "highway")}",\n')
        f.write(f'    .gas_preference = "{default_prefs.get("gas_preference", "cheapest")}",\n')
        f.write(f'    .morning_routine = "{default_prefs.get("morning_routine", "workout")}",\n')
        f.write(f'    .break_activity = "{default_prefs.get("break_activity", "quick_walk")}",\n')
        f.write(f'    .evening_activity = "{default_prefs.get("evening_activity", "relax")}",\n')
        f.write(f'    .podcast_continue = {1 if default_prefs.get("podcast_continue", True) else 0},\n')
        f.write(f'    .parking_spot = "{default_prefs.get("parking_spot", "usual_entrance")}"\n')
        f.write('};\n\n')
        
        # Write weights (same as before)
        f.write(f'// Input to Hidden Layer Weights [{hidden_size}x{input_size}]\n')
        f.write(f'static const float UC_W_INPUT_HIDDEN[UC_HIDDEN_SIZE][UC_INPUT_SIZE] = {{\n')
        for i in range(hidden_size):
            f.write('    {')
            for j in range(input_size):
                f.write(f'{W_ih[i,j]:.6f}f')
                if j < input_size - 1:
                    f.write(', ')
            f.write('}')
            if i < hidden_size - 1:
                f.write(',\n')
            else:
                f.write('\n')
        f.write('};\n\n')
        
        f.write(f'// Input to Hidden Layer Biases [{hidden_size}]\n')
        f.write(f'static const float UC_B_INPUT_HIDDEN[UC_HIDDEN_SIZE] = {{\n    ')
        for i in range(hidden_size):
            f.write(f'{b_ih[i]:.6f}f')
            if i < hidden_size - 1:
                f.write(', ')
        f.write('\n};\n\n')
        
        f.write(f'// Hidden to Output Layer Weights [{output_size}x{hidden_size}]\n')
        f.write(f'static const float UC_W_HIDDEN_OUTPUT[UC_OUTPUT_SIZE][UC_HIDDEN_SIZE] = {{\n')
        for i in range(output_size):
            f.write('    {')
            for j in range(hidden_size):
                f.write(f'{W_ho[i,j]:.6f}f')
                if j < hidden_size - 1:
                    f.write(', ')
            f.write('}')
            if i < output_size - 1:
                f.write(',\n')
            else:
                f.write('\n')
        f.write('};\n\n')
        
        f.write(f'// Hidden to Output Layer Biases [{output_size}]\n')
        f.write(f'static const float UC_B_HIDDEN_OUTPUT[UC_OUTPUT_SIZE] = {{\n    ')
        for i in range(output_size):
            f.write(f'{b_ho[i]:.6f}f')
            if i < output_size - 1:
                f.write(', ')
        f.write('\n};\n\n')
        
        # Write inference function
        f.write('''
// LIF neuron dynamics
static inline float uc_lif_step(float current, float membrane, float beta) {
    membrane = beta * membrane + current;
    float spike = (membrane > 1.0f) ? 1.0f : 0.0f;
    if (spike > 0.0f) {
        membrane = 0.0f;
    }
    return membrane;
}

// SNN inference for use cases
static inline int uc_snn_predict(const float* input) {
    static float mem_hidden[UC_HIDDEN_SIZE];
    static float mem_output[UC_OUTPUT_SIZE];
    static float spike_counts[UC_OUTPUT_SIZE];
    
    const float BETA = 0.9f;
    
    // Initialize
    for (int i = 0; i < UC_HIDDEN_SIZE; i++) {
        mem_hidden[i] = 0.0f;
    }
    for (int i = 0; i < UC_OUTPUT_SIZE; i++) {
        mem_output[i] = 0.0f;
        spike_counts[i] = 0.0f;
    }
    
    // Run spiking dynamics
    for (int t = 0; t < UC_NUM_STEPS; t++) {
        // Hidden layer
        float spikes_hidden[UC_HIDDEN_SIZE];
        for (int i = 0; i < UC_HIDDEN_SIZE; i++) {
            float current = UC_B_INPUT_HIDDEN[i];
            for (int j = 0; j < UC_INPUT_SIZE; j++) {
                current += UC_W_INPUT_HIDDEN[i][j] * input[j];
            }
            mem_hidden[i] = uc_lif_step(current, mem_hidden[i], BETA);
            spikes_hidden[i] = (mem_hidden[i] == 0.0f && current > 1.0f) ? 1.0f : 0.0f;
        }
        
        // Output layer
        for (int i = 0; i < UC_OUTPUT_SIZE; i++) {
            float current = UC_B_HIDDEN_OUTPUT[i];
            for (int j = 0; j < UC_HIDDEN_SIZE; j++) {
                current += UC_W_HIDDEN_OUTPUT[i][j] * spikes_hidden[j];
            }
            mem_output[i] = uc_lif_step(current, mem_output[i], BETA);
            if (mem_output[i] == 0.0f && current > 1.0f) {
                spike_counts[i] += 1.0f;
            }
        }
    }
    
    // Return activity with highest spike count
    int max_idx = 0;
    float max_count = spike_counts[0];
    for (int i = 1; i < UC_OUTPUT_SIZE; i++) {
        if (spike_counts[i] > max_count) {
            max_count = spike_counts[i];
            max_idx = i;
        }
    }
    
    return max_idx;
}

// Extract context features for use case model
static inline void extract_usecase_features(
    int hour,
    int minute,
    int day_of_week,
    int energy,
    int engagement,
    int idle_minutes,
    int has_meeting,
    int recent_accepts,
    int recent_rejects,
    float* features)
{
    int is_weekend = (day_of_week >= 5) ? 1 : 0;
    
    features[0] = hour / 24.0f;
    features[1] = minute / 60.0f;
    features[2] = day_of_week / 7.0f;
    features[3] = energy / 100.0f;
    features[4] = engagement / 100.0f;
    features[5] = idle_minutes / 180.0f;  // Normalized to 3 hours
    features[6] = has_meeting ? 1.0f : 0.0f;
    features[7] = recent_accepts / 10.0f;
    features[8] = recent_rejects / 10.0f;
    features[9] = is_weekend ? 1.0f : 0.0f;
}

// Get proactive suggestion using neuromorphic SNN
static inline const char* get_snn_proactive_suggestion(
    int hour,
    int minute,
    int day_of_week,
    int energy,
    int engagement,
    int idle_minutes,
    int has_meeting,
    int recent_accepts,
    int recent_rejects)
{
    float features[UC_INPUT_SIZE];
    
    extract_usecase_features(
        hour, minute, day_of_week,
        energy, engagement, idle_minutes,
        has_meeting, recent_accepts, recent_rejects,
        features
    );
    
    int predicted_idx = uc_snn_predict(features);
    return ACTIVITY_NAMES[predicted_idx];
}

#endif // USECASE_SNN_WEIGHTS_H
''')
    
    print(f"✓ C header file generated: {output_path}")
    
    return output_path


def main():
    print("\n" + "="*70)
    print("EXPORT USE CASE MODEL TO MiniOS")
    print("="*70)
    
    # Load model
    checkpoint = load_usecase_model('minios_usecase_model.pth')
    
    # Extract weights
    weights = extract_weights(checkpoint)
    
    # Generate C file
    generate_c_header(checkpoint, weights)
    
    print("\n" + "="*70)
    print("✓ EXPORT COMPLETE!")
    print("="*70)
    print(f"\nFiles created:")
    print(f"  - ../kernel/usecase_snn_weights.h")
    print(f"\nModel features exported:")
    print(f"  ✓ Neuromorphic SNN (LIF neurons)")
    print(f"  ✓ Proactive suggestions")
    print(f"  ✓ Default preferences")
    print(f"  ✓ Context-aware logic")
    print(f"  ✓ {checkpoint['output_size']} activity types")
    print(f"\nNext steps:")
    print(f"  1. cd ..")
    print(f"  2. Update kernel to use usecase_snn_weights.h")
    print(f"  3. make clean && make iso-carplay")
    print(f"  4. make run-carplay")
    print()


if __name__ == "__main__":
    main()
