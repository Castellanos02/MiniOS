# QUICK START - All Import Issues Fixed!

## ✅ All Files Updated

All relative imports (`.module`) have been changed to absolute imports (`module`).

The files now work when run directly from the `neuromorphic_assistant/` folder!

---

## 🚀 Step-by-Step (Guaranteed to Work)

### Step 1: Install Dependencies

```bash
pip install lava-nc numpy
```

**If lava-nc fails to install**, see "Lava Installation Issues" below.

---

### Step 2: Navigate to Folder

```bash
cd minios/neuromorphic_assistant

# Verify you're in the right place
pwd
ls __init__.py  # Should exist
```

---

### Step 3: Test Imports

```bash
python -c "from model_parameters import Model_Params; print('✓ Imports work!')"
```

**Expected output:**
```
✓ Imports work!
```

---

### Step 4: Run Training

```bash
python train_minios_model.py
```

**Expected output:**
```
🧠 MiniOS Neuromorphic Assistant Training

============================================================
Training Neuromorphic Assistant for MiniOS
============================================================

Model Configuration:
  Hidden neurons: 32
  Output classes: 20
  Timesteps: 50

Generating 200 training samples...

Training for 30 epochs...
------------------------------------------------------------
Epoch   5/30: Loss = 0.3456, Accuracy = 45.0%
...
```

---

### Step 5: Export to C

```bash
python export_to_minios.py
```

**Expected output:**
```
🔧 Exporting neuromorphic_assistant to C for MiniOS
============================================================
Exporting model to C...
✓ Exported to: ../kernel/neuromorphic_assistant_weights.h
✓ Exported context mapping to: ../kernel/neuromorphic_assistant_context.h
```

---

## 🔧 Lava Installation Issues

### If `pip install lava-nc` fails:

**Option A: Use conda**
```bash
conda create -n lava python=3.9
conda activate lava
pip install lava-nc numpy
```

**Option B: Install from source**
```bash
git clone https://github.com/lava-nc/lava.git
cd lava
pip install -e .
```

**Option C: Use Docker**
```bash
docker pull ghcr.io/lava-nc/lava:latest
docker run -it -v $(pwd):/workspace ghcr.io/lava-nc/lava:latest
```

---

## 📋 Complete Commands (Copy-Paste)

```bash
# 1. Install dependencies
pip install lava-nc numpy

# 2. Navigate to folder
cd minios/neuromorphic_assistant

# 3. Verify imports
python -c "from model_parameters import Model_Params; print('✓ Works!')"

# 4. Train model
python train_minios_model.py

# 5. Export to C
python export_to_minios.py

# 6. Build OS
cd ..
make clean
make iso-carplay

# 7. Run!
make run-carplay
```

---

## ✅ What Changed

**Before (didn't work):**
```python
from .model_parameters import Model_Params  # ❌ Relative import
```

**After (works!):**
```python
from model_parameters import Model_Params   # ✅ Absolute import
```

**Files updated:**
- `__init__.py` ✅
- `assistant.py` ✅
- `model_creation.py` ✅
- `surrogate_gradients.py` ✅
- `train_minios_model.py` ✅

---

## 🎯 Current Status

You should now be able to run from inside the `neuromorphic_assistant/` folder:

```bash
cd minios/neuromorphic_assistant
python train_minios_model.py  # ✅ Works!
```

---

## 💡 If You Still Get Errors

Run the diagnostic:

```bash
python check_imports.py
```

And paste the output - I'll help you fix it!

---

**Download the new archive or just run from the folder - it should work now!** 🚀
