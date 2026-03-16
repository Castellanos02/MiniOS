#!/usr/bin/env python3
"""
Export neuromorphic_assistant model to C for MiniOS
"""

import numpy as np
import sys


def load_model(filepath="minios_activity_model.npz"):
    """Load trained model weights"""
    
    try:
        data = np.load(filepath, allow_pickle=True)
        return {
            'Weight_input_hidden': data['Weight_input_hidden'],
            'Weight_hidden_output': data['Weight_hidden_output'],
            'input_size': int(data['input_size']),
            'hidden_size': int(data['hidden_size']),
            'output_size': int(data['output_size']),
            'steps': int(data['steps']),
            'class_names': list(data['class_names']),
        }
    except FileNotFoundError:
        print(f"ERROR: Model file '{filepath}' not found!")
        print("Please run: python train_minios_model.py first")
        sys.exit(1)


def export_to_c_header(model_data, output_file="../kernel/neuromorphic_assistant_weights.h"):
    """Export model to C header file"""
    
    W_ih = model_data['Weight_input_hidden']
    W_ho = model_data['Weight_hidden_output']
    input_size = model_data['input_size']
    hidden_size = model_data['hidden_size']
    output_size = model_data['output_size']
    steps = model_data['steps']
    
    print(f"\nExporting model to C...")
    print(f"  Input size: {input_size}")
    print(f"  Hidden size: {hidden_size}")
    print(f"  Output size: {output_size}")
    print(f"  Timesteps: {steps}")
    print(f"  Total weights: {W_ih.size + W_ho.size}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("// Auto-generated from neuromorphic_assistant\n")
        f.write("// MiniOS Activity Suggestion Model\n")
        f.write("// DO NOT EDIT MANUALLY\n\n")
        f.write("#ifndef NEUROMORPHIC_ASSISTANT_WEIGHTS_H\n")
        f.write("#define NEUROMORPHIC_ASSISTANT_WEIGHTS_H\n\n")
        
        # Architecture constants
        f.write("// ========== Network Architecture ==========\n")
        f.write(f"#define NA_INPUT_SIZE {input_size}\n")
        f.write(f"#define NA_HIDDEN_SIZE {hidden_size}\n")
        f.write(f"#define NA_OUTPUT_SIZE {output_size}\n")
        f.write(f"#define NA_TIMESTEPS {steps}\n\n")
        
        # Rate encoding parameters (from model_creation.py)
        f.write("// ========== Rate Encoding Parameters ==========\n")
        f.write("#define NA_MAX_FIRING_RATE 500.0f  // Hz\n")
        f.write("#define NA_TIME_STEP 1.0f          // ms\n\n")
        
        # Input -> Hidden weights
        f.write("// ========== Input -> Hidden Weights ==========\n")
        f.write(f"// Shape: [{hidden_size}, {input_size}]\n")
        f.write(f"static float na_weight_input_hidden[{W_ih.size}] = {{\n")
        
        flat_ih = W_ih.flatten()
        for i, w in enumerate(flat_ih):
            f.write(f"    {w:.8f}f")
            if i < len(flat_ih) - 1:
                f.write(",")
            if (i + 1) % 6 == 0:
                f.write("\n")
        f.write("\n};\n\n")
        
        # Hidden -> Output weights
        f.write("// ========== Hidden -> Output Weights ==========\n")
        f.write(f"// Shape: [{output_size}, {hidden_size}]\n")
        f.write(f"static float na_weight_hidden_output[{W_ho.size}] = {{\n")
        
        flat_ho = W_ho.flatten()
        for i, w in enumerate(flat_ho):
            f.write(f"    {w:.8f}f")
            if i < len(flat_ho) - 1:
                f.write(",")
            if (i + 1) % 6 == 0:
                f.write("\n")
        f.write("\n};\n\n")
        
        # Helper macros
        f.write("// ========== Helper Macros ==========\n")
        f.write("#define NA_GET_WEIGHT_IH(row, col) \\\n")
        f.write(f"    na_weight_input_hidden[(row) * NA_INPUT_SIZE + (col)]\n\n")
        f.write("#define NA_GET_WEIGHT_HO(row, col) \\\n")
        f.write(f"    na_weight_hidden_output[(row) * NA_HIDDEN_SIZE + (col)]\n\n")
        
        # Activity names (for debugging)
        f.write("// ========== Activity Class Names ==========\n")
        f.write("static const char* na_activity_names[] = {\n")
        for i, name in enumerate(model_data['class_names']):
            f.write(f"    \"{name}\"")
            if i < len(model_data['class_names']) - 1:
                f.write(",")
            f.write("\n")
        f.write("};\n\n")
        
        f.write("#endif // NEUROMORPHIC_ASSISTANT_WEIGHTS_H\n")
    
    print(f"\n✓ Exported to: {output_file}")
    print(f"  Size: {(W_ih.size + W_ho.size) * 4 / 1024:.2f} KB")


def export_context_mapping(output_file="../kernel/neuromorphic_assistant_context.h"):
    """Export context mapping code"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("// Context mapping from MiniOS to neuromorphic_assistant format\n")
        f.write("#ifndef NEUROMORPHIC_ASSISTANT_CONTEXT_H\n")
        f.write("#define NEUROMORPHIC_ASSISTANT_CONTEXT_H\n\n")
        f.write("#include <stdint.h>\n\n")
        
        f.write("// Map MiniOS features to neuromorphic_assistant input\n")
        f.write("void na_encode_minios_context(\n")
        f.write("    float* output,              // Output array [NA_INPUT_SIZE]\n")
        f.write("    uint8_t hour,               // Hour (0-23)\n")
        f.write("    uint8_t minute,             // Minute (0-59)\n")
        f.write("    uint8_t energy,             // Energy (0-100)\n")
        f.write("    uint8_t engagement,         // Engagement (0-100)\n")
        f.write("    float idle_time,            // Idle time (normalized)\n")
        f.write("    uint8_t recent_accepts,     // Recent accepts\n")
        f.write("    uint8_t recent_rejects      // Recent rejects\n")
        f.write(") {\n")
        f.write("    // Based on personal_model.py encode_input()\n")
        f.write("    int idx = 0;\n\n")
        
        f.write("    // Intent encoding (8 features)\n")
        f.write("    // [other, music, gas, reroute, meeting, email, text, location]\n")
        f.write("    for (int i = 0; i < 8; i++) {\n")
        f.write("        output[idx++] = (i == 0) ? 1.0f : 0.0f;  // Default: 'other'\n")
        f.write("    }\n\n")
        
        f.write("    // Dialog state (4 features)\n")
        f.write("    // [idle, asking, confirming, followup]\n")
        f.write("    for (int i = 0; i < 4; i++) {\n")
        f.write("        output[idx++] = (i == 0) ? 1.0f : 0.0f;  // Default: 'idle'\n")
        f.write("    }\n\n")
        
        f.write("    // Time/calendar (4 features)\n")
        f.write("    output[idx++] = hour / 24.0f;                    // hour_of_day\n")
        f.write("    output[idx++] = 0.0f;                            // is_weekend (TODO)\n")
        f.write("    output[idx++] = 0.0f;                            // in_commute\n")
        f.write("    output[idx++] = (engagement > 70) ? 1.0f : 0.0f; // busy_now\n\n")
        
        f.write("    // Candidate (12 features)\n")
        f.write("    // [9 candidate types + 3 extras]\n")
        f.write("    for (int i = 0; i < 9; i++) {\n")
        f.write("        output[idx++] = (i == 0) ? 1.0f : 0.0f;  // Default: 'none'\n")
        f.write("    }\n")
        f.write("    output[idx++] = energy / 100.0f;              // extra1: energy\n")
        f.write("    output[idx++] = recent_accepts / 10.0f;       // extra2: accepts\n")
        f.write("    output[idx++] = recent_rejects / 10.0f;       // extra3: rejects\n")
        f.write("}\n\n")
        
        f.write("#endif // NEUROMORPHIC_ASSISTANT_CONTEXT_H\n")
    
    print(f"✓ Exported context mapping to: {output_file}")


if __name__ == "__main__":
    print("\n🔧 Exporting neuromorphic_assistant to C for MiniOS\n")
    print("=" * 60)
    
    # Load trained model
    model_data = load_model("minios_activity_model.npz")
    
    # Export to C headers
    export_to_c_header(model_data)
    export_context_mapping()
    
    print("\n" + "=" * 60)
    print("✓ Export complete!")
    print("\nNext steps:")
    print("  1. cd ..")
    print("  2. make clean")
    print("  3. make iso-carplay")
    print("  4. make run-carplay")
    print()
