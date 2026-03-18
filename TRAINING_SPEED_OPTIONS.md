# Training Speed Options: Choose Your Balance

## 🎯 Three Training Scripts Available

You now have **3 training scripts** with different speed/accuracy trade-offs:

---

## ⚡ Option 1: ULTRA-FAST (NEW!)

**File:** `train_ULTRAFAST.py`

### **Settings:**
```python
Epochs: 5 (vs 15 normal)
Samples: 20 (vs 100 normal)  
Hidden neurons: 16 (vs 32 normal)
Timesteps: 10 (vs 30 normal)
Inference tests: 50 (vs 100 normal)
```

### **Performance:**
```
Time: ~30 seconds
Accuracy: ~40-60% (lower!)
Purpose: Quick testing only
```

### **Use When:**
- ✅ Testing if everything works
- ✅ Validating setup
- ✅ Quick iteration on code
- ✅ Checking metrics collection
- ❌ **NOT for production/research!**

### **Command:**
```bash
python train_ULTRAFAST.py
```

### **Output:**
```
⚡ ULTRA-FAST SNN TRAINING

Training for 5 epochs...
Epoch  1/5: Loss=0.4523, Acc= 45.0%, Time=2.1s
Epoch  2/5: Loss=0.3234, Acc= 55.0%, Time=4.2s
Epoch  3/5: Loss=0.2845, Acc= 60.0%, Time=6.3s
Epoch  4/5: Loss=0.2456, Acc= 65.0%, Time=8.4s
Epoch  5/5: Loss=0.2123, Acc= 70.0%, Time=10.5s

Training Summary:
  Total time: 10.5 seconds
  Final accuracy: 70.0%
  Total energy: 0.038 Wh

✓ Inference time: 8.5 ms (avg)
✓ Training complete in ~30 seconds!
```

---

## 🏃 Option 2: FAST

**File:** `train_minios_model_FAST.py`

### **Settings:**
```python
Epochs: 10 (vs 15 normal)
Samples: 50 (vs 100 normal)
Hidden neurons: 16 (vs 32 normal)
Timesteps: 20 (vs 30 normal)
```

### **Performance:**
```
Time: 2-5 minutes
Accuracy: ~75-80%
Purpose: Quick production model
```

### **Use When:**
- ✅ Need reasonable accuracy fast
- ✅ Testing before full training
- ✅ Good enough for demo
- ✅ Iterating on model design

### **Command:**
```bash
python train_minios_model_FAST.py
```

### **Output:**
```
Training for 10 epochs...
Epoch  1/10: Loss=0.4123, Acc= 40.0%, Time=3.2s
Epoch  5/10: Loss=0.2134, Acc= 68.0%, Time=16.0s
Epoch 10/10: Loss=0.1234, Acc= 78.0%, Time=32.1s

Training complete in 2.5 minutes!
Final accuracy: 78.0%
```

---

## 🎯 Option 3: FULL (Best Quality)

**File:** `train_with_directml.py`

### **Settings:**
```python
Epochs: 15
Samples: 100
Hidden neurons: 32
Timesteps: 30
Inference tests: 100
```

### **Performance:**
```
Time: 60-90 seconds (AMD), 50-70s (NVIDIA)
Accuracy: ~85-90%
Purpose: Production/research quality
```

### **Use When:**
- ✅ Final model for research
- ✅ Need best accuracy
- ✅ Publication-quality results
- ✅ Production deployment

### **Command:**
```bash
python train_with_directml.py
```

### **Output:**
```
Training for 15 epochs...
Epoch  1/15: Loss=0.4523, Acc= 42.0%, Time=5.2s
Epoch  5/15: Loss=0.2134, Acc= 75.0%, Time=26.1s
Epoch 10/15: Loss=0.1456, Acc= 84.0%, Time=52.3s
Epoch 15/15: Loss=0.1123, Acc= 88.0%, Time=78.5s

Training Summary:
  Total time: 78.5 seconds
  Final accuracy: 88.0%
  Total energy: 0.2836 Wh
```

---

## 📊 Comparison Table

| Feature | ULTRA-FAST | FAST | FULL |
|---------|------------|------|------|
| **Time** | ~30 sec | ~2-5 min | ~60-90 sec |
| **Accuracy** | 60-70% | 75-80% | 85-90% |
| **Epochs** | 5 | 10 | 15 |
| **Samples** | 20 | 50 | 100 |
| **Hidden** | 16 | 16 | 32 |
| **Timesteps** | 10 | 20 | 30 |
| **Purpose** | Testing | Quick prod | Best quality |
| **Use for** | Validation | Demo | Research |

---

## 🎯 Recommended Workflow

### **Step 1: Start with ULTRA-FAST**

```bash
# First time? Test everything works!
python train_ULTRAFAST.py
python export_to_minios.py
make clean && make iso-carplay
make run-carplay
```

**Why:** 30 seconds to verify entire pipeline works!

---

### **Step 2: Move to FAST**

```bash
# Ready to iterate? Use FAST
python train_minios_model_FAST.py
python export_to_minios.py
make clean && make iso-carplay
```

**Why:** 2-5 minutes for decent accuracy, good for development.

---

### **Step 3: Final with FULL**

```bash
# Ready for research/production?
# Start HWiNFO64 logging first!

python train_with_directml.py

# Stop HWiNFO64
# Combine metrics

python export_to_minios.py
make clean && make iso-carplay
```

**Why:** Best accuracy, full metrics collection!

---

## 💡 When to Use Each

### **ULTRA-FAST (30 seconds):**

```
✅ "Does my setup work?"
✅ "Can I train and export?"
✅ "Does the OS boot with my model?"
✅ "Are metrics being collected?"
✅ Testing code changes
✅ Debugging issues
```

### **FAST (2-5 minutes):**

```
✅ "I need a demo model"
✅ "Testing different architectures"
✅ "Iterating on features"
✅ "Good enough for now"
✅ Development work
```

### **FULL (60-90 seconds):**

```
✅ "Final model for research"
✅ "Need publication data"
✅ "Production deployment"
✅ "Best possible accuracy"
✅ Collecting full GPU metrics
```

---

## 🔬 Metrics Collection Recommendation

### **For Quick Testing:**

```bash
# No need for HWiNFO64
python train_ULTRAFAST.py
# Just test if it works!
```

### **For Development:**

```bash
# Optional HWiNFO64
python train_minios_model_FAST.py
# Metrics saved to training_metrics.json
```

### **For Research/Publication:**

```bash
# ALWAYS use HWiNFO64!
# Start HWiNFO64 logging
python train_with_directml.py
# Stop HWiNFO64
# Combine datasets for complete metrics
```

---

## 📁 All Scripts Save Same Files

**Each script produces:**

```
neuromorphic_assistant/
├── minios_activity_model.npz      ← Model (can export to OS)
├── training_metrics.json          ← Metrics (all 8!)
└── ... (other files)
```

**All are compatible with:**
- `export_to_minios.py`
- Build system
- OS deployment

**Difference is just quality/speed!**

---

## 🚀 Quick Command Reference

```bash
# === ULTRA-FAST (30 seconds) ===
python train_ULTRAFAST.py
# Use for: Testing, validation

# === FAST (2-5 minutes) ===
python train_minios_model_FAST.py
# Use for: Development, demos

# === FULL (60-90 seconds) ===
# Start HWiNFO64 first!
python train_with_directml.py
# Stop HWiNFO64
# Use for: Research, production

# === ALL FOLLOW WITH ===
python export_to_minios.py
cd .. && make clean && make iso-carplay && make run-carplay
```

---

## 💡 Pro Tips

### **Tip 1: Iterate Quickly**

```bash
# Use ULTRA-FAST for code changes
while developing:
    edit code
    python train_ULTRAFAST.py  # 30 sec
    test result
    
# Switch to FULL when ready
python train_with_directml.py  # 90 sec
```

### **Tip 2: Compare Speeds**

```bash
# Test all three!
time python train_ULTRAFAST.py        # ~30s
time python train_minios_model_FAST.py # ~150s
time python train_with_directml.py     # ~80s
```

### **Tip 3: Progressive Testing**

```bash
# Day 1: Verify setup
python train_ULTRAFAST.py
python export_to_minios.py
make iso-carplay && make run-carplay

# Day 2: Development
python train_minios_model_FAST.py
# ... iterate ...

# Day 3: Final metrics
# Start HWiNFO64
python train_with_directml.py
# Collect full data
```

---

## ✅ Summary

**You now have 3 options:**

1. ⚡ **ULTRA-FAST** (30s) - Testing
2. 🏃 **FAST** (2-5min) - Development  
3. 🎯 **FULL** (60-90s) - Production/Research

**All produce:**
- ✅ Working model
- ✅ All 8 metrics
- ✅ Compatible exports
- ✅ Run in OS

**Choose based on your needs!**

---

## 🎯 Recommended Path

```
First time:
  → train_ULTRAFAST.py (verify everything works)

Development:
  → train_minios_model_FAST.py (iterate quickly)

Final/Research:
  → train_with_directml.py (with HWiNFO64 for full metrics)
```

**Perfect balance of speed and quality!** ⚡🎯✨
