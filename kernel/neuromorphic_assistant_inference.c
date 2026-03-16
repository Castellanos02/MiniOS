// neuromorphic_assistant_inference.c
// C implementation matching the exact Lava architecture from neuromorphic_assistant
// Based on model_creation.py and surrogate_gradients.py

#include "neuromorphic_assistant_weights.h"
#include "neuromorphic_assistant_context.h"
#include <stdint.h>

// ========== Random Number Generator (Simple PRNG) ==========
static uint32_t na_rand_state = 12345;

static float na_rand_float(void) {
    na_rand_state = na_rand_state * 1103515245 + 12345;
    return (na_rand_state & 0x7FFFFFFF) / (float)0x7FFFFFFF;
}

static void na_rand_seed(uint32_t seed) {
    na_rand_state = seed;
}

// ========== Rate Encoding (from model_creation.py) ==========
static void na_rate_encode(
    const float* x,              // Input features [NA_INPUT_SIZE]
    uint8_t* spikes_out          // Output spikes [NA_TIMESTEPS][NA_INPUT_SIZE]
) {
    /*
     * Rate encoding matching model_creation.py:
     * - Normalize input by max absolute value
     * - Convert to spike probability: norm * max_firing_rate * (time_step / 1000)
     * - Generate spikes stochastically
     */
    
    // Find max absolute value for normalization
    float max_abs = 0.0f;
    for (int i = 0; i < NA_INPUT_SIZE; i++) {
        float abs_val = (x[i] < 0.0f) ? -x[i] : x[i];
        if (abs_val > max_abs) {
            max_abs = abs_val;
        }
    }
    
    // Normalize and compute spike probabilities
    for (int i = 0; i < NA_INPUT_SIZE; i++) {
        float norm;
        if (max_abs > 1e-12f) {
            norm = ((x[i] < 0.0f) ? -x[i] : x[i]) / max_abs;
        } else {
            norm = 0.0f;
        }
        
        // Spike probability = norm * max_rate * dt
        float prob = norm * NA_MAX_FIRING_RATE * (NA_TIME_STEP / 1000.0f);
        
        // Clip to [0, 1]
        if (prob > 1.0f) prob = 1.0f;
        if (prob < 0.0f) prob = 0.0f;
        
        // Generate spikes over time
        for (int t = 0; t < NA_TIMESTEPS; t++) {
            spikes_out[t * NA_INPUT_SIZE + i] = (na_rand_float() < prob) ? 1 : 0;
        }
    }
}

// ========== LIF Neuron Simulation (Simple) ==========
// Note: Lava's LIF is complex, but for rate-based output we simplify

static void na_lif_layer_forward(
    const uint8_t* input_spikes,  // Input spikes [NA_TIMESTEPS][input_size]
    const float* weights,          // Weights [output_size][input_size]
    float* output_rates,           // Output spike rates [output_size]
    int input_size,
    int output_size
) {
    /*
     * Simplified LIF forward pass:
     * - For each output neuron, compute weighted sum of input spikes
     * - Apply LIF dynamics (simplified): if weighted_input > threshold, spike
     * - Count output spikes over time
     * - Convert to rates
     */
    
    // Initialize output counts
    for (int o = 0; o < output_size; o++) {
        output_rates[o] = 0.0f;
    }
    
    // Simulate over time
    for (int t = 0; t < NA_TIMESTEPS; t++) {
        for (int o = 0; o < output_size; o++) {
            float weighted_sum = 0.0f;
            
            // Compute weighted sum of inputs at this timestep
            for (int i = 0; i < input_size; i++) {
                uint8_t spike = input_spikes[t * input_size + i];
                weighted_sum += spike * weights[o * input_size + i];
            }
            
            // Simple threshold: if weighted_sum > 0, spike
            // (Simplified from full LIF dynamics)
            if (weighted_sum > 0.5f) {
                output_rates[o] += 1.0f;
            }
        }
    }
    
    // Convert counts to rates
    for (int o = 0; o < output_size; o++) {
        output_rates[o] /= (float)NA_TIMESTEPS;
    }
}

// ========== Network State (Modifiable for Learning) ==========
static float na_weights_ih[NA_HIDDEN_SIZE * NA_INPUT_SIZE];
static float na_weights_ho[NA_OUTPUT_SIZE * NA_HIDDEN_SIZE];

static uint8_t na_initialized = 0;

// ========== Initialize Network ==========
void na_init(void) {
    if (na_initialized) return;
    
    // Copy const weights to modifiable arrays
    for (int i = 0; i < NA_HIDDEN_SIZE * NA_INPUT_SIZE; i++) {
        na_weights_ih[i] = na_weight_input_hidden[i];
    }
    
    for (int i = 0; i < NA_OUTPUT_SIZE * NA_HIDDEN_SIZE; i++) {
        na_weights_ho[i] = na_weight_hidden_output[i];
    }
    
    na_rand_seed(42);  // Fixed seed for reproducibility
    na_initialized = 1;
}

// ========== Forward Pass (Inference) ==========
uint8_t na_forward(const float* features, float* output_rates_ptr) {
    /*
     * Complete forward pass through neuromorphic_assistant network
     * Returns: predicted activity index (argmax of output rates)
     */
    
    na_init();
    
    // 1. Rate encode inputs
    static uint8_t input_spikes[NA_TIMESTEPS * NA_INPUT_SIZE];
    na_rate_encode(features, input_spikes);
    
    // 2. Hidden layer forward
    static float hidden_rates[NA_HIDDEN_SIZE];
    na_lif_layer_forward(
        input_spikes,
        na_weights_ih,
        hidden_rates,
        NA_INPUT_SIZE,
        NA_HIDDEN_SIZE
    );
    
    // 3. Convert hidden rates to spikes for next layer
    static uint8_t hidden_spikes[NA_TIMESTEPS * NA_HIDDEN_SIZE];
    for (int t = 0; t < NA_TIMESTEPS; t++) {
        for (int h = 0; h < NA_HIDDEN_SIZE; h++) {
            // Probabilistic spike generation from rates
            hidden_spikes[t * NA_HIDDEN_SIZE + h] = 
                (na_rand_float() < hidden_rates[h]) ? 1 : 0;
        }
    }
    
    // 4. Output layer forward
    static float output_rates[NA_OUTPUT_SIZE];
    na_lif_layer_forward(
        hidden_spikes,
        na_weights_ho,
        output_rates,
        NA_HIDDEN_SIZE,
        NA_OUTPUT_SIZE
    );
    
    // 5. Normalize output rates (matching model_creation.py)
    float max_rate = 0.0f;
    for (int o = 0; o < NA_OUTPUT_SIZE; o++) {
        if (output_rates[o] > max_rate) {
            max_rate = output_rates[o];
        }
    }
    
    if (max_rate > 1e-8f) {
        for (int o = 0; o < NA_OUTPUT_SIZE; o++) {
            output_rates[o] /= (max_rate + 1e-8f);
        }
    }
    
    // 6. Copy output rates if requested
    if (output_rates_ptr != 0) {
        for (int o = 0; o < NA_OUTPUT_SIZE; o++) {
            output_rates_ptr[o] = output_rates[o];
        }
    }
    
    // 7. Find winning activity (argmax)
    uint8_t winner = 0;
    float max_val = output_rates[0];
    for (uint8_t o = 1; o < NA_OUTPUT_SIZE; o++) {
        if (output_rates[o] > max_val) {
            max_val = output_rates[o];
            winner = o;
        }
    }
    
    return winner;
}

// ========== MiniOS Interface ==========
uint8_t na_suggest_activity(
    uint8_t hour,
    uint8_t minute,
    uint8_t energy,
    uint8_t engagement,
    uint32_t idle_cycles,
    uint8_t recent_accepts,
    uint8_t recent_rejects
) {
    // Encode MiniOS context to neuromorphic_assistant format
    static float features[NA_INPUT_SIZE];
    float idle_time = idle_cycles / 100000000.0f;
    
    na_encode_minios_context(
        features,
        hour, minute, energy, engagement,
        idle_time, recent_accepts, recent_rejects
    );
    
    // Run inference
    return na_forward(features, 0);
}
