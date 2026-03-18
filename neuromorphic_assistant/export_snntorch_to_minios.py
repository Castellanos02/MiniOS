#!/usr/bin/env python3
"""
Export snnTorch model to MiniOS C code
Converts PyTorch SNN to lightweight C implementation
"""

import torch
import numpy as np
import json
import os


def load_snntorch_model(model_path='minios_snn_model.pth'):
    """Load trained snnTorch model"""
    
    print(f"\n{'='*70}")
    print(f"LOADING snnTorch MODEL")
    print(f"{'='*70}")
    
    checkpoint = torch.load(model_path, map_location='cpu')
    
    print(f"✓ Model loaded from: {model_path}")
    print(f"  Input size: {checkpoint['input_size']}")
    print(f"  Hidden size: {checkpoint['hidden_size']}")
    print(f"  Output size: {checkpoint['output_size']}")
    print(f"  Classes: {len(checkpoint['class_names'])}")
    
    return checkpoint


def extract_weights(checkpoint):
    """Extract weights from PyTorch model"""
    
    state_dict = checkpoint['model_state_dict']
    
    # Extract layer weights
    W_input_hidden = state_dict['fc1.weight'].numpy()  # [hidden, input]
    b_input_hidden = state_dict['fc1.bias'].numpy()    # [hidden]
    
    W_hidden_output = state_dict['fc2.weight'].numpy() # [output, hidden]
    b_hidden_output = state_dict['fc2.bias'].numpy()   # [output]
    
    print(f"\n✓ Weights extracted:")
    print(f"  Input->Hidden: {W_input_hidden.shape}")
    print(f"  Hidden->Output: {W_hidden_output.shape}")
    
    return {
        'W_input_hidden': W_input_hidden,
        'b_input_hidden': b_input_hidden,
        'W_hidden_output': W_hidden_output,
        'b_hidden_output': b_hidden_output,
    }


def generate_c_header(checkpoint, weights, output_path='../kernel/neuromorphic_snntorch_weights.h'):
    """Generate C header file with weights"""
    
    print(f"\n{'='*70}")
    print(f"GENERATING C HEADER FILE")
    print(f"{'='*70}")
    
    input_size = checkpoint['input_size']
    hidden_size = checkpoint['hidden_size']
    output_size = checkpoint['output_size']
    class_names = checkpoint['class_names']
    
    W_ih = weights['W_input_hidden']
    b_ih = weights['b_input_hidden']
    W_ho = weights['W_hidden_output']
    b_ho = weights['b_hidden_output']
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"""/* 
 * Neuromorphic SNN Weights - snnTorch Export
 * Generated from trained Leaky Integrate-and-Fire model
 * 
 * Architecture:
 * - Input: {input_size} features
 * - Hidden: {hidden_size} LIF neurons
 * - Output: {output_size} classes
 * 
 * Neuromorphic properties:
 * - Spiking neurons with membrane dynamics
 * - Temporal processing over multiple timesteps
 * - Event-driven computation
 */

#ifndef NEUROMORPHIC_SNNTORCH_WEIGHTS_H
#define NEUROMORPHIC_SNNTORCH_WEIGHTS_H

#define SNN_INPUT_SIZE {input_size}
#define SNN_HIDDEN_SIZE {hidden_size}
#define SNN_OUTPUT_SIZE {output_size}
#define SNN_NUM_STEPS 20  // Timesteps for inference (reduced for speed)

// Activity class names
static const char* ACTIVITY_NAMES[SNN_OUTPUT_SIZE] = {{
""")
        
        # Write class names
        for i, name in enumerate(class_names):
            f.write(f'    "{name}"')
            if i < len(class_names) - 1:
                f.write(',\n')
            else:
                f.write('\n')
        f.write('};\n\n')
        
        # Write input->hidden weights
        f.write(f'// Input to Hidden Layer Weights [{hidden_size}x{input_size}]\n')
        f.write(f'static const float W_INPUT_HIDDEN[SNN_HIDDEN_SIZE][SNN_INPUT_SIZE] = {{\n')
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
        
        # Write input->hidden biases
        f.write(f'// Input to Hidden Layer Biases [{hidden_size}]\n')
        f.write(f'static const float B_INPUT_HIDDEN[SNN_HIDDEN_SIZE] = {{\n    ')
        for i in range(hidden_size):
            f.write(f'{b_ih[i]:.6f}f')
            if i < hidden_size - 1:
                f.write(', ')
        f.write('\n};\n\n')
        
        # Write hidden->output weights
        f.write(f'// Hidden to Output Layer Weights [{output_size}x{hidden_size}]\n')
        f.write(f'static const float W_HIDDEN_OUTPUT[SNN_OUTPUT_SIZE][SNN_HIDDEN_SIZE] = {{\n')
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
        
        # Write hidden->output biases
        f.write(f'// Hidden to Output Layer Biases [{output_size}]\n')
        f.write(f'static const float B_HIDDEN_OUTPUT[SNN_OUTPUT_SIZE] = {{\n    ')
        for i in range(output_size):
            f.write(f'{b_ho[i]:.6f}f')
            if i < output_size - 1:
                f.write(', ')
        f.write('\n};\n\n')
        
        # Write inference function
        f.write('''
// Leaky Integrate-and-Fire (LIF) neuron dynamics
static inline float lif_step(float current, float membrane, float beta) {
    // Membrane potential decay
    membrane = beta * membrane + current;
    
    // Spike generation (threshold = 1.0)
    float spike = (membrane > 1.0f) ? 1.0f : 0.0f;
    
    // Reset after spike
    if (spike > 0.0f) {
        membrane = 0.0f;
    }
    
    return membrane;
}

// SNN forward inference with spiking dynamics
static inline int snn_predict(const float* input) {
    static float mem_hidden[SNN_HIDDEN_SIZE];
    static float mem_output[SNN_OUTPUT_SIZE];
    static float spike_counts[SNN_OUTPUT_SIZE];
    
    const float BETA = 0.9f;  // Membrane decay constant
    
    // Initialize
    for (int i = 0; i < SNN_HIDDEN_SIZE; i++) {
        mem_hidden[i] = 0.0f;
    }
    for (int i = 0; i < SNN_OUTPUT_SIZE; i++) {
        mem_output[i] = 0.0f;
        spike_counts[i] = 0.0f;
    }
    
    // Run for multiple timesteps (spiking dynamics)
    for (int t = 0; t < SNN_NUM_STEPS; t++) {
        // Hidden layer
        float spikes_hidden[SNN_HIDDEN_SIZE];
        for (int i = 0; i < SNN_HIDDEN_SIZE; i++) {
            // Weighted sum
            float current = B_INPUT_HIDDEN[i];
            for (int j = 0; j < SNN_INPUT_SIZE; j++) {
                current += W_INPUT_HIDDEN[i][j] * input[j];
            }
            
            // LIF dynamics
            mem_hidden[i] = lif_step(current, mem_hidden[i], BETA);
            spikes_hidden[i] = (mem_hidden[i] == 0.0f && current > 1.0f) ? 1.0f : 0.0f;
        }
        
        // Output layer
        for (int i = 0; i < SNN_OUTPUT_SIZE; i++) {
            // Weighted sum from spikes
            float current = B_HIDDEN_OUTPUT[i];
            for (int j = 0; j < SNN_HIDDEN_SIZE; j++) {
                current += W_HIDDEN_OUTPUT[i][j] * spikes_hidden[j];
            }
            
            // LIF dynamics
            mem_output[i] = lif_step(current, mem_output[i], BETA);
            
            // Count spikes
            if (mem_output[i] == 0.0f && current > 1.0f) {
                spike_counts[i] += 1.0f;
            }
        }
    }
    
    // Return class with highest spike count
    int max_idx = 0;
    float max_count = spike_counts[0];
    for (int i = 1; i < SNN_OUTPUT_SIZE; i++) {
        if (spike_counts[i] > max_count) {
            max_count = spike_counts[i];
            max_idx = i;
        }
    }
    
    return max_idx;
}

#endif // NEUROMORPHIC_SNNTORCH_WEIGHTS_H
''')
    
    print(f"✓ C header file generated: {output_path}")
    print(f"  Total size: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    return output_path


def generate_context_mapping(output_path='../kernel/neuromorphic_snntorch_context.h'):
    """Generate context feature extraction code"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("""/*
 * MiniOS Context to SNN Features Mapping
 * Converts OS state to neural network input
 */

#ifndef NEUROMORPHIC_SNNTORCH_CONTEXT_H
#define NEUROMORPHIC_SNNTORCH_CONTEXT_H

#include "neuromorphic_snntorch_weights.h"

// Extract features from MiniOS context
static inline void extract_snn_features(
    int hour,
    int minute,
    int energy,
    int engagement,
    float idle_time,
    int recent_accepts,
    int recent_rejects,
    float* features)
{
    features[0] = hour / 24.0f;                          // Normalized hour
    features[1] = minute / 60.0f;                        // Normalized minute
    features[2] = energy / 100.0f;                       // Normalized energy
    features[3] = engagement / 100.0f;                   // Normalized engagement
    features[4] = idle_time;                             // Idle time ratio
    features[5] = recent_accepts / 10.0f;                // Normalized accepts
    features[6] = recent_rejects / 10.0f;                // Normalized rejects
    features[7] = (hour >= 9 && hour < 17) ? 1.0f : 0.0f;  // Work hours
    features[8] = (hour >= 20 || hour < 6) ? 1.0f : 0.0f;  // Rest hours
    features[9] = (energy > 70) ? 1.0f : 0.0f;           // High energy
}

// Get activity suggestion using SNN
static inline const char* get_snn_suggestion(
    int hour,
    int minute,
    int energy,
    int engagement,
    float idle_time,
    int recent_accepts,
    int recent_rejects)
{
    float features[SNN_INPUT_SIZE];
    
    // Extract features
    extract_snn_features(
        hour, minute, energy, engagement,
        idle_time, recent_accepts, recent_rejects,
        features
    );
    
    // Run SNN inference
    int predicted_idx = snn_predict(features);
    
    // Return activity name
    return ACTIVITY_NAMES[predicted_idx];
}

#endif // NEUROMORPHIC_SNNTORCH_CONTEXT_H
""")
    
    print(f"✓ Context mapping generated: {output_path}")


def main():
    print("\n" + "="*70)
    print("EXPORT snnTorch MODEL TO MiniOS")
    print("="*70)
    
    # Load model
    checkpoint = load_snntorch_model('minios_snn_model.pth')
    
    # Extract weights
    weights = extract_weights(checkpoint)
    
    # Generate C files
    weights_file = generate_c_header(checkpoint, weights)
    generate_context_mapping()
    
    print("\n" + "="*70)
    print("✓ EXPORT COMPLETE!")
    print("="*70)
    print(f"\nFiles created:")
    print(f"  - {weights_file}")
    print(f"  - ../kernel/neuromorphic_snntorch_context.h")
    print(f"\nNext steps:")
    print(f"  1. cd ..")
    print(f"  2. make clean && make iso-carplay")
    print(f"  3. make run-carplay")
    print()


if __name__ == "__main__":
    main()
