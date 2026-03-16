// neuromorphic_assistant_learning.c
// Online learning implementation matching surrogate_gradients.py
// Policy gradient learning with reward signals

#include "neuromorphic_assistant_inference.c"
#include <stdint.h>

// ========== Learning Parameters ==========
#define NA_LEARNING_RATE 0.01f
#define NA_EPSILON 1e-8f

// ========== Last Inference State (for learning) ==========
static float na_last_features[NA_INPUT_SIZE];
static float na_last_hidden_rates[NA_HIDDEN_SIZE];
static float na_last_output_rates[NA_OUTPUT_SIZE];
static uint8_t na_last_prediction = 0;
static uint8_t na_state_saved = 0;

// ========== Softmax (from learning.py) ==========
static void na_softmax(const float* logits, float* probs, int size) {
    // Find max for numerical stability
    float max_logit = logits[0];
    for (int i = 1; i < size; i++) {
        if (logits[i] > max_logit) {
            max_logit = logits[i];
        }
    }
    
    // Compute exp(logit - max)
    float sum = 0.0f;
    for (int i = 0; i < size; i++) {
        probs[i] = 1.0f;  // Simplified exp approximation
        // In real implementation: probs[i] = expf(logits[i] - max_logit);
        // For embedded, we simplify
        float shifted = logits[i] - max_logit;
        if (shifted < -10.0f) {
            probs[i] = 0.0f;
        } else if (shifted > 0.0f) {
            probs[i] = 1.0f + shifted;
        } else {
            probs[i] = 1.0f + shifted * 0.5f;
        }
        sum += probs[i];
    }
    
    // Normalize
    for (int i = 0; i < size; i++) {
        probs[i] /= (sum + NA_EPSILON);
    }
}

// ========== Feedback to Reward (from learning.py) ==========
static float na_feedback_to_reward(uint8_t accepted) {
    // feedback_to_reward() from learning.py
    // accept -> +1.0, reject -> -1.0
    return accepted ? 1.0f : -1.0f;
}

// ========== Policy Gradient (from learning.py) ==========
static void na_compute_policy_gradient(
    const float* output_rates,
    uint8_t action_idx,
    float reward,
    float* grad_out  // Output gradient [NA_OUTPUT_SIZE]
) {
    /*
     * Policy gradient from learning.py:
     * loss = -reward * log(p_action)
     * grad = -reward * (one_hot - probs)
     */
    
    // Compute softmax probabilities
    static float probs[NA_OUTPUT_SIZE];
    na_softmax(output_rates, probs, NA_OUTPUT_SIZE);
    
    // Compute gradient: -reward * (one_hot - probs)
    for (int o = 0; o < NA_OUTPUT_SIZE; o++) {
        float one_hot = (o == action_idx) ? 1.0f : 0.0f;
        grad_out[o] = -reward * (one_hot - probs[o]);
    }
}

// ========== Weight Update (from surrogate_update) ==========
static void na_update_weights(
    const float* hidden_rates,
    const float* output_rates,
    uint8_t action_idx,
    float reward,
    float learning_rate
) {
    /*
     * Weight update from surrogate_gradients.py:
     * grad_W = outer(grad_out, hidden_rates)
     * Weight_hidden_output -= lr * grad_W
     */
    
    // Compute output gradient
    static float grad_out[NA_OUTPUT_SIZE];
    na_compute_policy_gradient(output_rates, action_idx, reward, grad_out);
    
    // Update hidden→output weights
    // W[o, h] -= lr * grad_out[o] * hidden_rates[h]
    for (int o = 0; o < NA_OUTPUT_SIZE; o++) {
        for (int h = 0; h < NA_HIDDEN_SIZE; h++) {
            float gradient = grad_out[o] * hidden_rates[h];
            na_weights_ho[o * NA_HIDDEN_SIZE + h] -= learning_rate * gradient;
        }
    }
}

// ========== Enhanced Forward with State Saving ==========
static uint8_t na_forward_and_save_state(const float* features) {
    /*
     * Run forward pass and save intermediate states for learning
     */
    
    na_init();
    
    // Save input features
    for (int i = 0; i < NA_INPUT_SIZE; i++) {
        na_last_features[i] = features[i];
    }
    
    // 1. Rate encode
    static uint8_t input_spikes[NA_TIMESTEPS * NA_INPUT_SIZE];
    na_rate_encode(features, input_spikes);
    
    // 2. Hidden layer
    na_lif_layer_forward(
        input_spikes,
        na_weights_ih,
        na_last_hidden_rates,
        NA_INPUT_SIZE,
        NA_HIDDEN_SIZE
    );
    
    // 3. Hidden spikes
    static uint8_t hidden_spikes[NA_TIMESTEPS * NA_HIDDEN_SIZE];
    for (int t = 0; t < NA_TIMESTEPS; t++) {
        for (int h = 0; h < NA_HIDDEN_SIZE; h++) {
            hidden_spikes[t * NA_HIDDEN_SIZE + h] = 
                (na_rand_float() < na_last_hidden_rates[h]) ? 1 : 0;
        }
    }
    
    // 4. Output layer
    na_lif_layer_forward(
        hidden_spikes,
        na_weights_ho,
        na_last_output_rates,
        NA_HIDDEN_SIZE,
        NA_OUTPUT_SIZE
    );
    
    // 5. Normalize
    float max_rate = 0.0f;
    for (int o = 0; o < NA_OUTPUT_SIZE; o++) {
        if (na_last_output_rates[o] > max_rate) {
            max_rate = na_last_output_rates[o];
        }
    }
    
    if (max_rate > NA_EPSILON) {
        for (int o = 0; o < NA_OUTPUT_SIZE; o++) {
            na_last_output_rates[o] /= (max_rate + NA_EPSILON);
        }
    }
    
    // 6. Find winner
    uint8_t winner = 0;
    float max_val = na_last_output_rates[0];
    for (uint8_t o = 1; o < NA_OUTPUT_SIZE; o++) {
        if (na_last_output_rates[o] > max_val) {
            max_val = na_last_output_rates[o];
            winner = o;
        }
    }
    
    na_last_prediction = winner;
    na_state_saved = 1;
    
    return winner;
}

// ========== Online Learning Interface ==========
uint8_t na_suggest_with_learning(
    uint8_t hour, uint8_t minute, uint8_t energy,
    uint8_t engagement, uint32_t idle_cycles,
    uint8_t recent_accepts, uint8_t recent_rejects
) {
    // Encode context
    static float features[NA_INPUT_SIZE];
    float idle_time = idle_cycles / 100000000.0f;
    
    na_encode_minios_context(
        features,
        hour, minute, energy, engagement,
        idle_time, recent_accepts, recent_rejects
    );
    
    // Forward pass with state saving
    return na_forward_and_save_state(features);
}

void na_learn_from_feedback(uint8_t accepted) {
    /*
     * Update weights based on user feedback
     * Implements surrogate_update() from surrogate_gradients.py
     */
    
    if (!na_state_saved) {
        return;  // No previous prediction to learn from
    }
    
    // Convert feedback to reward
    float reward = na_feedback_to_reward(accepted);
    
    if (reward == 0.0f) {
        return;  // Ignore feedback (though we only have accept/reject)
    }
    
    // Update weights using policy gradient
    na_update_weights(
        na_last_hidden_rates,
        na_last_output_rates,
        na_last_prediction,
        reward,
        NA_LEARNING_RATE
    );
    
    // Clear state
    na_state_saved = 0;
}

// ========== Get Activity Name ==========
const char* na_get_activity_name(uint8_t activity_idx) {
    if (activity_idx >= NA_OUTPUT_SIZE) {
        return "unknown";
    }
    return na_activity_names[activity_idx];
}
