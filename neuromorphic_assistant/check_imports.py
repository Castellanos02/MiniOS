#!/usr/bin/env python3
"""
Diagnostic script to check why imports are failing
"""

import sys
import os

print("=" * 60)
print("DIAGNOSTIC CHECK FOR NEUROMORPHIC_ASSISTANT")
print("=" * 60)

# 1. Check Python version
print(f"\n1. Python Version: {sys.version}")
print(f"   Executable: {sys.executable}")

# 2. Check current directory
print(f"\n2. Current Directory: {os.getcwd()}")

# 3. Check if files exist
print(f"\n3. Files in current directory:")
files = os.listdir('.')
for f in sorted(files):
    if f.endswith('.py'):
        print(f"   ✓ {f}")

# 4. Check if __init__.py exists
if '__init__.py' in files:
    print(f"\n4. __init__.py: ✓ Found")
else:
    print(f"\n4. __init__.py: ✗ NOT FOUND")

# 5. Try importing local modules one by one
print(f"\n5. Testing imports:")

modules_to_test = [
    'model_parameters',
    'assistant',
    'model_creation',
    'inference',
    'learning',
    'surrogate_gradients',
    'personal_model',
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f"   ✓ {module}")
    except ImportError as e:
        print(f"   ✗ {module} - ERROR: {e}")

# 6. Check for dependencies
print(f"\n6. Checking dependencies:")

# Check numpy
try:
    import numpy
    print(f"   ✓ numpy {numpy.__version__}")
except ImportError:
    print(f"   ✗ numpy - NOT INSTALLED")

# Check lava
try:
    import lava
    print(f"   ✓ lava")
except ImportError as e:
    print(f"   ✗ lava - NOT INSTALLED")
    print(f"      Error: {e}")
    print(f"\n   SOLUTION: Run 'pip install lava-nc'")

# 7. Check sys.path
print(f"\n7. Python search paths:")
for i, path in enumerate(sys.path[:5]):
    print(f"   [{i}] {path}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
