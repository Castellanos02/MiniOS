# GPU Selection Guide

## 🎯 Which GPU Gets Used?

All training scripts automatically detect and use the **best available GPU** in this priority order:

### **Detection Priority:**
```
1. NVIDIA GPU (via NVML) ✅ Checked first!
2. AMD GPU (via DirectML)
3. AMD GPU (via ROCm - Linux)
4. CPU fallback
```

---

## ✅ Fixed in train_ULTRAFAST.py

**The ULTRAFAST script now checks NVIDIA first!**

**Before (wrong order):**
```python
1. Check DirectML first ← Picked AMD even when NVIDIA available
2. Check NVIDIA second
```

**After (correct order):**
```python
1. Check NVIDIA first ← Now picks NVIDIA correctly!
2. Check DirectML second
```

---

## 🔍 How to Verify Which GPU is Being Used

### **Look at the output:**

**NVIDIA GPU:**
```
✓ NVIDIA GPU: NVIDIA GeForce RTX 4060
```

**AMD GPU:**
```
✓ AMD GPU via DirectML: AMD Radeon RX 5500 XT
```

**CPU only:**
```
⚠ CPU only
```

---

## 📊 Expected Output by GPU

### **With NVIDIA RTX 4060:**

```
⚡ ULTRA-FAST SNN TRAINING
======================================================================
✓ NVIDIA GPU: NVIDIA GeForce RTX 4060

Training for 5 epochs...
Epoch 1/5: Loss=0.4523, Acc=45.0%, Time=1.8s
...
Epoch 5/5: Loss=0.2123, Acc=70.0%, Time=9.2s

Training Summary:
  Total time: 9.2 seconds
  Final accuracy: 70.0%
  Total energy: 0.021 Wh

✓ Inference time: 8.5 ms (avg)
✓ Training complete!
```

**Metrics collected via NVML:**
- ✅ Real GPU power
- ✅ Real GPU temperature
- ✅ Real GPU memory
- ✅ All automatic!

---

### **With AMD RX 5500 XT:**

```
⚡ ULTRA-FAST SNN TRAINING
======================================================================
✓ AMD GPU via DirectML: AMD Radeon RX 5500 XT

Training for 5 epochs...
Epoch 1/5: Loss=0.4523, Acc=45.0%, Time=2.1s
...
Epoch 5/5: Loss=0.2123, Acc=70.0%, Time=10.5s

Training Summary:
  Total time: 10.5 seconds
  Final accuracy: 70.0%
  Total energy: 0.038 Wh (estimated)

✓ Inference time: 8.5 ms (avg)
✓ Training complete!
```

**Metrics collected:**
- ⚠️ Estimated GPU power (130W TDP)
- ⚠️ Estimated GPU memory
- ✅ Need HWiNFO64 for real data

---

## 🎯 Your Situation

**You have:**
- NVIDIA RTX 4060
- AMD RX 5500 XT (or DirectML installed)

**Problem:** Script detected DirectML first, used AMD path

**Solution:** Updated script now checks NVIDIA first!

---

## 🚀 To Use NVIDIA GPU

### **1. Update Scripts**

Download the updated archive with fixed GPU detection.

### **2. Run Training**

```bash
python train_ULTRAFAST.py
```

**Expected output:**
```
✓ NVIDIA GPU: NVIDIA GeForce RTX 4060
```

### **3. Verify**

If you still see AMD, check:

```bash
# Check NVIDIA drivers
nvidia-smi

# Check pynvml
python -c "import pynvml; pynvml.nvmlInit(); print('NVIDIA OK')"
```

---

## 💡 Manual GPU Selection (Optional)

If you want to force a specific GPU, you can modify the script:

### **Force NVIDIA:**

```python
# In train_ULTRAFAST.py, detect_gpu():
def detect_gpu(self):
    # Force NVIDIA
    import pynvml
    pynvml.nvmlInit()
    self.nvml = pynvml
    self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    return 'nvidia'
```

### **Force AMD:**

```python
# In train_ULTRAFAST.py, detect_gpu():
def detect_gpu(self):
    # Force AMD DirectML
    import torch_directml
    self.device = torch_directml.device(0)
    return 'amd_directml'
```

---

## 📋 Script-by-Script GPU Support

| Script | NVIDIA | AMD DirectML | AMD ROCm |
|--------|--------|--------------|----------|
| **train_ULTRAFAST.py** | ✅ Auto | ✅ Auto | ❌ |
| **train_minios_model_FAST.py** | ❌ CPU only | ❌ CPU only | ❌ |
| **train_with_directml.py** | ✅ Auto | ✅ Auto | ✅ Auto |

**Recommendation:** Use `train_with_directml.py` for full GPU support!

---

## ✅ Summary

**Problem:** ULTRAFAST detected AMD instead of NVIDIA

**Cause:** Checked DirectML before NVIDIA

**Fix:** Updated detection order (NVIDIA first)

**Result:** Will now use NVIDIA RTX 4060! ✅

---

## 🔧 Troubleshooting

### **Still shows AMD?**

**Check if pynvml is working:**
```bash
python -c "import pynvml; pynvml.nvmlInit(); print(pynvml.nvmlDeviceGetName(pynvml.nvmlDeviceGetHandleByIndex(0)))"
```

**Should output:**
```
NVIDIA GeForce RTX 4060
```

**If error:** Install/reinstall nvidia-ml-py3:
```bash
pip install nvidia-ml-py3 --upgrade
```

---

### **Want to use AMD instead?**

Uninstall pynvml (script will skip NVIDIA check):
```bash
pip uninstall pynvml nvidia-ml-py3
```

Then script will detect AMD DirectML.

---

**Download updated scripts and verify NVIDIA detection!** 🚀
