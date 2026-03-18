# Neuromorphic Assistant Integration Instructions

## 🎯 Complete Integration Steps

Your `neuromorphic_assistant` is now integrated into MiniOS!

---

## 📁 Files Added

### In `neuromorphic_assistant/` folder:
- `__init__.py` - Package initialization
- `assistant.py` - Main PersonalAssistant class
- `model_creation.py` - Lava SNN creation
- `model_parameters.py` - Model configuration
- `inference.py` - Forward pass
- `learning.py` - Feedback and gradients
- `surrogate_gradients.py` - Policy gradient learning
- `personal_model.py` - Input encoding
- `pretraining.py` - Pretraining utilities
- `train_minios_model.py` - **Training script for MiniOS**
- `export_to_minios.py` - **Export trained model to C**

### In `kernel/` folder:
- `neuromorphic_assistant_weights.h` - (Generated) Model weights
- `neuromorphic_assistant_context.h` - (Generated) Context mapping
- `neuromorphic_assistant_inference.c` - C inference engine
- `neuromorphic_assistant_learning.c` - Online learning

---

## 🚀 Step-by-Step Build Process

### Step 1: Train the Model

```bash
cd minios/neuromorphic_assistant

# Install dependencies (if needed)
pip install numpy lava-nc

# Train model for MiniOS activities
python train_minios_model.py
```

**Output:**
```
Training Neuromorphic Assistant for MiniOS
...
Epoch  30/30: Loss = 0.1234, Accuracy = 85.0%
Training complete!
✓ Model saved to: minios_activity_model.npz
```

---

### Step 2: Export to C

```bash
# Still in neuromorphic_assistant/ folder
python export_to_minios.py
```

**Output:**
```
Exporting model to C...
✓ Exported to: ../kernel/neuromorphic_assistant_weights.h
✓ Exported context mapping to: ../kernel/neuromorphic_assistant_context.h
```

**This creates:**
- `kernel/neuromorphic_assistant_weights.h` - Your trained weights
- `kernel/neuromorphic_assistant_context.h` - Context encoding

---

### Step 3: Modify kernel_carplay.c

```bash
cd ..  # Back to minios/
nano kernel/kernel_carplay.c
```

**Add at the top (after existing includes):**

```c
// Include neuromorphic_assistant
#include "neuromorphic_assistant_learning.c"

// Learning statistics
static uint32_t na_total_accepts = 0;
static uint32_t na_total_rejects = 0;
```

**In `kernel_main()`, add after initialization:**

```c
// Initialize neuromorphic assistant
na_init();

draw_text("Neuromorphic Assistant Ready!", 20, 3,
         (COLOR_BLACK << 4) | COLOR_LIGHT_GREEN);

char info[80];
simple_sprintf(info, "Model: %d -> %d -> %d neurons",
               NA_INPUT_SIZE, NA_HIDDEN_SIZE, NA_OUTPUT_SIZE);
draw_text(info, 20, 4, (COLOR_BLACK << 4) | COLOR_LIGHT_CYAN);
```

**Replace `ml_suggest_activity()` function:**

```c
static uint8_t ml_suggest_activity(void) {
    // Use neuromorphic_assistant for suggestions
    return na_suggest_with_learning(
        g_ml.current_hour,
        g_ml.current_minute,
        g_ml.energy_level,
        g_ml.engagement,
        g_ml.idle_cycles,
        na_total_accepts,
        na_total_rejects
    );
}
```

**In notification handling (when user accepts):**

```c
if (key == 'y') {
    // ... existing code ...
    
    // LEARN from acceptance
    na_learn_from_feedback(1);  // 1 = accepted
    na_total_accepts++;
    
    draw_text("Learning from your choice...", 14, 17,
             (COLOR_LIGHT_GREEN << 4) | COLOR_WHITE);
    
    // ... rest of code ...
}
```

**When user rejects:**

```c
else if (key == 'n') {
    // LEARN from rejection
    na_learn_from_feedback(0);  // 0 = rejected
    na_total_rejects++;
    
    draw_text("Learning from feedback...", 14, 16,
             (COLOR_LIGHT_RED << 4) | COLOR_WHITE);
    
    // ... rest of code ...
}
```

**Save the file**

---

### Step 4: Build MiniOS

```bash
# Clean previous builds
make clean

# Build with neuromorphic_assistant
make iso-carplay
```

**Expected output:**
```
Building CarPlay-style kernel...
gcc ... kernel_carplay.c ...
  (includes neuromorphic_assistant_learning.c)
  (includes neuromorphic_assistant_inference.c)
  (includes neuromorphic_assistant_weights.h)
✓ Built CarPlay kernel
✓ Created: build/minios_carplay.iso
```

---

### Step 5: Run!

```bash
make run-carplay
```

**QEMU opens with your neuromorphic OS!**

---

## 🎮 Testing Your Model

### What You'll See

**Boot:**
```
╔═══════════════════════════════════════╗
║ MiniOS CarPlay                       ║
╠═══════════════════════════════════════╣
║ Neuromorphic Assistant Ready!        ║
║ Model: 28 -> 32 -> 20 neurons       ║
╚═══════════════════════════════════════╝
```

**First Notification (08:50):**
```
Suggestion: [Activity from YOUR trained model]
[Y] Accept  [N] Dismiss
```

**Press Y:**
```
✓ Suggestion accepted!
✓ Learning from your choice...  ← YOUR model learning!
✓ Added to calendar!
```

**Press N:**
```
✗ Suggestion dismissed
✓ Learning from feedback...  ← YOUR model adapting!
```

---

## 🧠 How Your Model Works in the OS

### Architecture Flow

```
MiniOS Context (hour, energy, etc.)
        ↓
na_encode_minios_context()
        ↓
Your trained features [28 dims]
        ↓
Rate encoding (matching your model)
        ↓
RingBuffer → Dense → LIF → Dense → LIF
        ↓
Output rates [20 activities]
        ↓
Argmax → Suggested activity
        ↓
User accepts/rejects
        ↓
Policy gradient update (your surrogate_update)
        ↓
Weights updated in real-time!
```

### Learning Process

Your model uses **policy gradient** learning (from `surrogate_gradients.py`):

1. **Forward pass** saves hidden and output rates
2. **User feedback** converts to reward (+1.0 or -1.0)
3. **Compute gradient**: `grad = -reward * (one_hot - softmax(output))`
4. **Update weights**: `W_ho -= lr * outer(grad, hidden_rates)`

**This is YOUR exact learning algorithm running in the OS!**

---

## 📊 Activity Classes

Your model suggests from these 20 activities:

```
0:  rest                9:  deep_work          18: focus_session
1:  workout            10: light_task          19: free_time
2:  creative_work      11: brainstorm
3:  study              12: organize
4:  practice_skill     13: learn_something
5:  social_activity    14: physical_activity
6:  plan_day           15: mental_exercise
7:  review_goals       16: relax
8:  quick_break        17: energize
```

---

## ✅ Verification Checklist

**After building, confirm:**

- [ ] Training completed successfully
- [ ] Export created `.h` files
- [ ] Kernel compiles without errors
- [ ] ISO created (~6 MB)
- [ ] OS boots with "Neuromorphic Assistant Ready!"
- [ ] Suggestions appear
- [ ] "Learning from your choice..." shows on accept
- [ ] "Learning from feedback..." shows on reject

---

## 🔧 Troubleshooting

### Training Fails

**Error:** `ModuleNotFoundError: No module named 'lava'`

**Solution:**
```bash
pip install lava-nc numpy
```

### Export Fails

**Error:** `Model file not found`

**Solution:**
```bash
# Make sure you ran training first
python train_minios_model.py
# Then export
python export_to_minios.py
```

### Build Errors

**Error:** `neuromorphic_assistant_weights.h: No such file`

**Solution:**
```bash
# Re-run export
cd neuromorphic_assistant
python export_to_minios.py
cd ..
make clean
make iso-carplay
```

### No Learning Message

**Solution:**
- Verify you added learning callbacks in kernel_carplay.c
- Check that `na_learn_from_feedback()` is called
- Rebuild: `make clean && make iso-carplay`

---

## 🎯 Quick Command Summary

```bash
# Complete workflow
cd minios/neuromorphic_assistant
python train_minios_model.py    # Train
python export_to_minios.py      # Export
cd ..
# (Edit kernel_carplay.c - add integration code)
make clean                       # Clean
make iso-carplay                 # Build
make run-carplay                 # Run!
```

---

## 🎉 Success!

**You now have:**
- ✅ YOUR Lava SNN running in MiniOS
- ✅ YOUR training code
- ✅ YOUR policy gradient learning
- ✅ Real-time weight updates
- ✅ Personalized activity suggestions

**This is YOUR neuromorphic_assistant in a bootable OS!** 🧠⚡

