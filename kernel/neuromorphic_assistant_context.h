// Context mapping from MiniOS to neuromorphic_assistant format
#ifndef NEUROMORPHIC_ASSISTANT_CONTEXT_H
#define NEUROMORPHIC_ASSISTANT_CONTEXT_H

#include <stdint.h>

// Map MiniOS features to neuromorphic_assistant input
void na_encode_minios_context(
    float* output,              // Output array [NA_INPUT_SIZE]
    uint8_t hour,               // Hour (0-23)
    uint8_t minute,             // Minute (0-59)
    uint8_t energy,             // Energy (0-100)
    uint8_t engagement,         // Engagement (0-100)
    float idle_time,            // Idle time (normalized)
    uint8_t recent_accepts,     // Recent accepts
    uint8_t recent_rejects      // Recent rejects
) {
    // Based on personal_model.py encode_input()
    int idx = 0;

    // Intent encoding (8 features)
    // [other, music, gas, reroute, meeting, email, text, location]
    for (int i = 0; i < 8; i++) {
        output[idx++] = (i == 0) ? 1.0f : 0.0f;  // Default: 'other'
    }

    // Dialog state (4 features)
    // [idle, asking, confirming, followup]
    for (int i = 0; i < 4; i++) {
        output[idx++] = (i == 0) ? 1.0f : 0.0f;  // Default: 'idle'
    }

    // Time/calendar (4 features)
    output[idx++] = hour / 24.0f;                    // hour_of_day
    output[idx++] = 0.0f;                            // is_weekend (TODO)
    output[idx++] = 0.0f;                            // in_commute
    output[idx++] = (engagement > 70) ? 1.0f : 0.0f; // busy_now

    // Candidate (12 features)
    // [9 candidate types + 3 extras]
    for (int i = 0; i < 9; i++) {
        output[idx++] = (i == 0) ? 1.0f : 0.0f;  // Default: 'none'
    }
    output[idx++] = energy / 100.0f;              // extra1: energy
    output[idx++] = recent_accepts / 10.0f;       // extra2: accepts
    output[idx++] = recent_rejects / 10.0f;       // extra3: rejects
}

#endif // NEUROMORPHIC_ASSISTANT_CONTEXT_H
