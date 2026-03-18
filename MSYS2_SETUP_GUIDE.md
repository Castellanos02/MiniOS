# MSYS2 Setup Guide for MiniOS (Windows)

## 🎯 Good News: You Don't Need Ubuntu!

**MSYS2 can build and run MiniOS directly on Windows!**

You already have MSYS2 installed, so you're 90% of the way there. Just need to install a few packages.

---

## 🚀 Quick Setup (MSYS2)

### Step 1: Open MSYS2 Terminal

**Important:** Use **MSYS2 MINGW64** terminal (not MSYS2 MSYS)

1. Press Windows key
2. Type "MSYS2 MINGW64"
3. Open the terminal

---

### Step 2: Update MSYS2

```bash
# Update package database (NO sudo needed!)
pacman -Syu
```

**Press Y when asked**, then **close and reopen** MSYS2 terminal.

```bash
# Update remaining packages
pacman -Su
```

---

### Step 3: Install Build Tools

**Install GCC, NASM, Make:**

```bash
pacman -S mingw-w64-x86_64-gcc nasm make
```

**Press Y to install**

**Install QEMU (emulator):**

```bash
pacman -S mingw-w64-x86_64-qemu
```

**Install GRUB tools:**

```bash
pacman -S grub xorriso
```

---

### Step 4: Verify Installation

```bash
gcc --version
# Should show: gcc.exe (Rev...) 13.x or higher

nasm --version  
# Should show: NASM version 2.x

make --version
# Should show: GNU Make 4.x

qemu-system-x86_64 --version
# Should show: QEMU emulator version 8.x or higher

grub-mkrescue --version
# Should show: grub-mkrescue (GRUB) 2.x
```

**If all commands work, you're ready!**

---

### Step 5: Navigate to MiniOS

```bash
# MSYS2 can access Windows drives as /c/, /d/, etc.
# Example: C:\Users\Axel\Downloads\minios

cd /c/Users/Axel\ Castellanos/Downloads/test/virtualboxandqemu/minios
```

**Or wherever you extracted minios.tar.gz**

---

### Step 6: Build MiniOS

```bash
# Clean previous builds
make clean

# Build the CarPlay ISO
make iso-carplay
```

**Expected output:**
```
Building CarPlay-style kernel...
✓ Built CarPlay kernel
Creating CarPlay ISO...
✓ Created: build/minios_carplay.iso
```

---

### Step 7: Run MiniOS

```bash
make run-carplay
```

**QEMU window should open with your OS!**

---

## 🔧 Complete MSYS2 Installation Commands

**All in one (copy-paste friendly):**

```bash
# Update MSYS2
pacman -Syu
# Close terminal after this, then reopen

# Install build tools
pacman -S mingw-w64-x86_64-gcc nasm make mingw-w64-x86_64-qemu grub xorriso

# Navigate to project
cd /c/Users/YOUR_USERNAME/path/to/minios

# Build
make clean
make iso-carplay

# Run
make run-carplay
```

---

## 🆚 MSYS2 vs Ubuntu Comparison

| Feature | MSYS2 | Ubuntu |
|---------|-------|--------|
| **OS** | Windows | Linux |
| **Package Manager** | pacman | apt |
| **Sudo** | ❌ Not needed | ✅ Required |
| **Drive Access** | /c/, /d/ | /mnt/c/, /mnt/d/ |
| **Build MiniOS** | ✅ Yes | ✅ Yes |
| **Run QEMU** | ✅ Yes | ✅ Yes |
| **Speed** | Fast | Fast |

**Both work perfectly! Use what you already have.**

---

## 🔍 Troubleshooting MSYS2

### Issue 1: "pacman: command not found"

**Cause:** Wrong terminal

**Solution:** Open **MSYS2 MINGW64** (not CMD or PowerShell)

### Issue 2: "gcc: command not found"

**Solution:**
```bash
pacman -S mingw-w64-x86_64-gcc
```

### Issue 3: "Permission denied"

**Cause:** MSYS2 doesn't use sudo

**Solution:** Just run the command directly (no sudo)
```bash
# WRONG (Ubuntu way):
sudo apt install gcc

# RIGHT (MSYS2 way):
pacman -S mingw-w64-x86_64-gcc
```

### Issue 4: Can't Find Files

**MSYS2 paths:**
```bash
# Windows: C:\Users\Axel\Downloads\minios
# MSYS2:   /c/Users/Axel/Downloads/minios

cd /c/Users/Axel/Downloads/minios
```

### Issue 5: Build Errors

```bash
# Make sure you're in the right directory
pwd
# Should show: /c/Users/.../minios

# List files
ls
# Should see: Makefile, kernel/, build/, etc.

# Clean and rebuild
make clean
make iso-carplay
```

---

## 🪟 If You Still Want Ubuntu (Optional)

If you want to install Ubuntu alongside Windows, you have two options:

### Option A: WSL (Windows Subsystem for Linux)

**Easiest way to run Ubuntu on Windows:**

1. **Enable WSL:**
   - Open PowerShell as Administrator
   - Run: `wsl --install`
   - Restart computer

2. **Install Ubuntu:**
   - Open Microsoft Store
   - Search "Ubuntu 22.04"
   - Install
   - Launch Ubuntu
   - Create username/password

3. **Install tools in Ubuntu:**
```bash
sudo apt update
sudo apt install -y build-essential nasm qemu-system-x86 grub-pc-bin grub-common xorriso
```

**Note:** QEMU GUI may not work well in WSL. Better to use MSYS2 for QEMU.

### Option B: Dual Boot (Advanced)

**Install Ubuntu alongside Windows:**

1. Download Ubuntu 22.04 ISO
2. Create bootable USB with Rufus
3. Restart computer
4. Boot from USB
5. Install Ubuntu (choose "Install alongside Windows")

**Not recommended unless you want a full Linux environment.**

---

## 💡 Recommended: Stick with MSYS2!

**Why MSYS2 is perfect for MiniOS:**

✅ **Already installed** - No extra setup
✅ **Native Windows** - Full performance  
✅ **No sudo needed** - Simpler commands
✅ **Direct file access** - Easy to navigate
✅ **QEMU works great** - Smooth emulation
✅ **Lightweight** - No VM overhead

**You can build and run MiniOS right now with what you have!**

---

## 🎯 Your Next Steps (MSYS2)

### 1. Open MSYS2 MINGW64 Terminal

Press Windows key → Type "MSYS2 MINGW64" → Enter

### 2. Install Tools

```bash
pacman -S mingw-w64-x86_64-gcc nasm make mingw-w64-x86_64-qemu grub xorriso
```

### 3. Navigate to MiniOS

```bash
cd /c/Users/Axel\ Castellanos/Downloads/test/virtualboxandqemu/minios
```

### 4. Build

```bash
make clean
make iso-carplay
```

### 5. Run

```bash
make run-carplay
```

---

## 📝 Quick Reference Card

**MSYS2 Commands (No sudo!):**

```bash
# Install packages
pacman -S <package>

# Update system
pacman -Syu

# Search for packages
pacman -Ss <name>

# Remove package
pacman -R <package>
```

**Path Conversion:**

```
Windows:  C:\Users\Axel\Downloads\minios
MSYS2:    /c/Users/Axel/Downloads/minios

Windows:  D:\Projects\test
MSYS2:    /d/Projects/test
```

**Essential Packages:**

```bash
pacman -S mingw-w64-x86_64-gcc     # C compiler
pacman -S nasm                      # Assembler
pacman -S make                      # Build tool
pacman -S mingw-w64-x86_64-qemu    # Emulator
pacman -S grub                      # Bootloader
pacman -S xorriso                   # ISO tool
```

---

## ✅ Installation Checklist

After setup, verify:

- [ ] MSYS2 MINGW64 terminal opens
- [ ] `gcc --version` works
- [ ] `nasm --version` works
- [ ] `make --version` works
- [ ] `qemu-system-x86_64 --version` works
- [ ] `grub-mkrescue --version` works
- [ ] Can navigate to minios directory
- [ ] `make clean` succeeds
- [ ] `make iso-carplay` builds ISO
- [ ] `make run-carplay` opens QEMU
- [ ] OS boots successfully

---

## 🎉 Summary

**You DON'T need Ubuntu!**

**What you have:** MSYS2 on Windows
**What you need:** A few packages (`gcc`, `nasm`, `qemu`, etc.)
**Time needed:** 5-10 minutes
**Result:** Build and run MiniOS on Windows!

**No dual-boot, no VM, no WSL needed - MSYS2 does everything!** 🚀

---

## 📞 Complete Setup Command

**Copy and paste this into MSYS2 MINGW64 terminal:**

```bash
# Install everything
pacman -S mingw-w64-x86_64-gcc nasm make mingw-w64-x86_64-qemu grub xorriso

# Navigate to your minios folder (adjust path!)
cd /c/Users/YOUR_USERNAME/path/to/minios

# Build
make clean && make iso-carplay

# Run
make run-carplay
```

**That's it! Your OS will boot in QEMU!** 🎉
