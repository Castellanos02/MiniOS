# Windows Encoding Error Fix

## 🐛 The Error

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 20: character maps to <undefined>
```

## 🎯 What Happened

The export script used Unicode arrow characters (→) which Windows console doesn't support by default.

## ✅ Fixed!

The export script has been updated to:
1. Use ASCII arrows (`->`) instead of Unicode (`→`)
2. Explicitly use UTF-8 encoding for file writes

## 🚀 Solution

### Option 1: Use Updated Script (Recommended)

The fixed version is already in the new archive. Just extract and use it:

```bash
# Extract new archive
tar -xzf minios.tar.gz
cd minios/neuromorphic_assistant

# Run export (now works on Windows!)
python export_to_minios.py
```

---

### Option 2: Manual Fix (If Using Old Version)

If you have the old script, edit `export_to_minios.py`:

**Line 66-67, change:**
```python
# FROM:
f.write("// ========== Input → Hidden Weights ==========\n")

# TO:
f.write("// ========== Input -> Hidden Weights ==========\n")
```

**Line 80-81, change:**
```python
# FROM:
f.write("// ========== Hidden → Output Weights ==========\n")

# TO:
f.write("// ========== Hidden -> Output Weights ==========\n")
```

**Line 47, change:**
```python
# FROM:
with open(output_file, 'w') as f:

# TO:
with open(output_file, 'w', encoding='utf-8') as f:
```

**Line 120, change:**
```python
# FROM:
with open(output_file, 'w') as f:

# TO:
with open(output_file, 'w', encoding='utf-8') as f:
```

---

### Option 3: Quick Environment Fix

Set Python to use UTF-8 encoding:

**PowerShell:**
```powershell
$env:PYTHONIOENCODING="utf-8"
python export_to_minios.py
```

**Command Prompt:**
```cmd
set PYTHONIOENCODING=utf-8
python export_to_minios.py
```

---

## ✅ Verify Fix

After applying fix, run:

```bash
python export_to_minios.py
```

**Should see:**
```
Exporting model to C...
  Input size: 28
  Hidden size: 32
  Output size: 20
  Timesteps: 30
  Total weights: 1280

✓ Exported to: ../kernel/neuromorphic_assistant_weights.h
  Size: 15.23 KB

✓ Exported context mapping to: ../kernel/neuromorphic_assistant_context.h
```

**No encoding errors!** ✅

---

## 🎯 Continue with Build

After successful export:

```bash
cd ..
make clean
make iso-carplay
make run-carplay
```

---

## 💡 Why This Happened

**Windows default console encoding:**
- Uses CP1252 (Windows-1252)
- Doesn't support all Unicode characters
- Arrows (→) not in CP1252 character set

**The fix:**
- Changed → to -> (ASCII)
- Added explicit UTF-8 encoding
- Now works on all systems!

---

## 🔧 Prevention

For future scripts on Windows, always:

```python
# Use UTF-8 encoding
with open(filename, 'w', encoding='utf-8') as f:
    f.write("content")

# Or set environment variable
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

---

**The updated archive has the fix - just re-extract and run!** 🚀
