# Fix for "ModuleNotFoundError: No module named 'neuromorphic_assistant'"

## 🔧 Quick Fixes (Choose One)

### Option 1: Run from the correct directory (Easiest)

```bash
# Make sure you're IN the neuromorphic_assistant directory
cd minios/neuromorphic_assistant

# Verify you're in the right place
ls
# Should see: __init__.py, assistant.py, train_minios_model.py, etc.

# Run training
python train_minios_model.py
```

---

### Option 2: Install as a package

```bash
cd minios/neuromorphic_assistant

# Install in development mode
pip install -e .

# Now you can run from anywhere
cd ..
python neuromorphic_assistant/train_minios_model.py
```

---

### Option 3: Set PYTHONPATH

```bash
# From minios directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

cd neuromorphic_assistant
python train_minios_model.py
```

---

### Option 4: Use the fixed script (Already done!)

The `train_minios_model.py` has been updated to work from the current directory automatically.

Just make sure you're in the right folder:

```bash
cd minios/neuromorphic_assistant
python train_minios_model.py
```

---

## ✅ Verification

**Before running, check:**

```bash
# Are you in the right directory?
pwd
# Should show: .../minios/neuromorphic_assistant

# Do the files exist?
ls *.py
# Should show: __init__.py, assistant.py, train_minios_model.py, etc.

# Try importing manually
python -c "from model_parameters import Model_Params; print('✓ Import works!')"
```

---

## 🚀 Complete Working Example

```bash
# 1. Navigate to the folder
cd ~/minios/neuromorphic_assistant  # Or wherever you extracted it

# 2. Verify location
pwd
ls __init__.py  # Should exist

# 3. Run training
python train_minios_model.py
```

---

## 📋 If You Still Get Errors

**Check Python version:**
```bash
python --version
# Should be Python 3.8 or higher
```

**Check if lava is installed:**
```bash
python -c "import lava; print('Lava installed!')"
```

**If not installed:**
```bash
pip install lava-nc numpy
```

**Full clean install:**
```bash
cd minios/neuromorphic_assistant
pip install -e .
python train_minios_model.py
```

---

## 💡 What the Fix Does

The updated `train_minios_model.py` now has:

```python
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from local files
from model_parameters import Model_Params
from assistant import PersonalAssistant
```

This makes it work regardless of where Python looks for modules!

---

## ✅ Expected Output

When it works, you'll see:

```
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
Epoch  10/30: Loss = 0.2134, Accuracy = 65.0%
...
```

---

**Try Option 1 first - just run from the neuromorphic_assistant directory!** 🚀
