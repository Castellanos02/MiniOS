# 🔧 Rebuild Instructions - Fix Time Bug

## The Issue

You're seeing **09:11** instead of **08:55** because you're running an old version of the kernel. The fix is in the code but needs to be compiled.

---

## ✅ Solution: Rebuild the ISO

### Step-by-Step

```bash
# 1. Navigate to minios directory
cd minios

# 2. Clean ALL previous builds
make clean

# 3. Rebuild the CarPlay ISO
make iso-carplay

# 4. Run the new version
make run-carplay
```

### Expected Output

**After `make clean`:**
```
rm -rf build/
✓ Cleaned
```

**After `make iso-carplay`:**
```
Building CarPlay-style kernel...
✓ Built CarPlay kernel
Creating CarPlay ISO...
✓ Created: build/minios_carplay.iso
```

**After `make run-carplay`:**
```
Starting CarPlay MiniOS in QEMU...
[QEMU window opens]
```

---

## 🎯 How to Test the Fix

### Complete Test Sequence

1. **Boot** → See home screen at 08:30
2. **Open Calendar** → Press Enter
3. **Wait ~2 minutes** → Time advances to 08:50
4. **Notification appears** → "Silence phone for meeting"
5. **Press Y** → Accept suggestion
6. **Look at calendar** → Should now show:

```
08:55  Silence phone for meeting  5 min  [AI] ← CORRECT!
09:00  Team Meeting              60 min  [  ]
```

**NOT 09:11 anymore!**

---

## 🔍 Verification

### Before Fix (What You're Seeing Now)
```
09:11  Silence phone for meeting  ← WRONG
```

### After Fix (What You Should See)
```
08:55  Silence phone for meeting  ← CORRECT
```

---

## 🐛 Why This Happened

### The Bug
```c
// Old code:
new_minute = evt->minute - 5;

// For 09:00:
new_minute = 0 - 5 = -5 (underflow to 251 as uint8_t)
// Eventually became 09:11 (corrupted)
```

### The Fix
```c
// New code:
if (minute >= 5) {
    minute -= 5;  // Simple case
} else {
    // Borrow from hour
    minute = minute + 60 - 5;  // 0 + 60 - 5 = 55
    hour -= 1;                  // 9 - 1 = 8
}
// Result: 08:55 ✓
```

---

## ⚠️ Common Issues

### Issue 1: Still Shows 09:11

**Cause:** Didn't rebuild
**Solution:** 
```bash
make clean
make iso-carplay
make run-carplay
```

### Issue 2: Build Errors

**Cause:** Old object files
**Solution:**
```bash
rm -rf build/
make iso-carplay
```

### Issue 3: QEMU Running Old Version

**Cause:** QEMU cached old ISO
**Solution:**
```bash
# Close QEMU window
# Then:
make clean
make iso-carplay
make run-carplay
```

---

## 📊 All Events - Expected Times

After the fix, accepted suggestions will appear at:

| Original Event | Suggestion Time | Difference |
|----------------|----------------|------------|
| 09:00 Team Meeting | **08:55** | -5 min ✓ |
| 11:30 Lunch Break | **11:25** | -5 min ✓ |
| 14:00 Project Work | **13:55** | -5 min ✓ |
| 16:30 Coffee Break | **16:25** | -5 min ✓ |

---

## ✅ Success Checklist

After rebuilding, verify:

- [ ] Ran `make clean`
- [ ] Ran `make iso-carplay` 
- [ ] Saw "✓ Created: build/minios_carplay.iso"
- [ ] Ran `make run-carplay`
- [ ] QEMU opened with fresh boot
- [ ] Accepted suggestion
- [ ] Calendar shows **08:55** (not 09:11)

---

## 🚀 Quick Commands

**Full rebuild and run:**
```bash
cd minios && make clean && make iso-carplay && make run-carplay
```

**Or use the archive:**
```bash
# Extract fresh copy
tar -xzf minios.tar.gz
cd minios
make iso-carplay
make run-carplay
```

---

## 💡 Pro Tip

**Always rebuild after getting new code:**
```bash
# After downloading new minios.tar.gz:
tar -xzf minios.tar.gz
cd minios
make clean  # Important!
make iso-carplay
make run-carplay
```

---

**After rebuilding, the time will be correct: 08:55!** ✅
