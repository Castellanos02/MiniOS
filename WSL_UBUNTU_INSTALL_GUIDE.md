# Complete WSL Ubuntu Installation Guide

## 🎯 Install Ubuntu on Windows with WSL

This will let you run Ubuntu alongside Windows without dual-booting or VirtualBox.

---

## 📋 Step-by-Step Instructions

### Step 1: Open PowerShell as Administrator

1. **Press Windows key**
2. **Type:** `PowerShell`
3. **Right-click** on "Windows PowerShell"
4. **Click:** "Run as administrator"
5. **Click "Yes"** when asked for permission

### Step 2: Install WSL

**In PowerShell (as admin), type:**

```powershell
wsl --install
```

**Press Enter**

**You should see:**
```
Installing: Windows Subsystem for Linux
Installing: Ubuntu
The requested operation is successful. Changes will not be effective until the system is rebooted.
```

### Step 3: Restart Your Computer

```powershell
# After WSL installation completes:
Restart-Computer
```

**Or manually restart:**
- Start Menu → Power → Restart

---

## 🐧 After Restart: Set Up Ubuntu

### Step 4: Ubuntu Will Launch Automatically

After restart, Ubuntu terminal will open automatically.

**You'll see:**
```
Installing, this may take a few minutes...
```

**Wait for it to finish.**

### Step 5: Create Ubuntu Username

**When prompted:**
```
Enter new UNIX username:
```

**Type a username** (lowercase, no spaces)
- Example: `axel`
- Press Enter

### Step 6: Create Password

```
New password:
```

**Type a password** (you won't see it as you type - this is normal)
- Press Enter

```
Retype new password:
```

**Type the same password again**
- Press Enter

**You're now in Ubuntu!**

You should see:
```
axel@DESKTOP-XXXXX:~$
```

---

## ✅ Step 7: Update Ubuntu

**In the Ubuntu terminal:**

```bash
sudo apt update
sudo apt upgrade -y
```

**Enter your password when asked**

**Wait for updates to complete** (2-5 minutes)

---

## 🔧 Step 8: Install Build Tools

**Copy and paste this entire block:**

```bash
sudo apt install -y build-essential nasm make qemu-system-x86 grub-pc-bin grub-common xorriso
```

**Press Enter, wait for installation** (5-10 minutes)

---

## 📁 Step 9: Access Your Windows Files

**WSL can access your Windows drives!**

```bash
# Your C: drive is at:
cd /mnt/c/

# Your Downloads folder:
cd /mnt/c/Users/YOUR_USERNAME/Downloads/

# Your MiniOS folder (example):
cd /mnt/c/Users/Axel\ Castellanos/Downloads/test/virtualboxandqemu/minios/
```

**Replace `Axel\ Castellanos` with your Windows username**

---

## 🏗️ Step 10: Build MiniOS in WSL

**Navigate to your minios directory:**

```bash
cd /mnt/c/Users/Axel\ Castellanos/Downloads/test/virtualboxandqemu/minios
```

**Build the ISO:**

```bash
make clean
make iso-carplay
```

**You should see:**
```
Building CarPlay-style kernel...
✓ Built CarPlay kernel
Creating CarPlay ISO...
✓ Created: build/minios_carplay.iso
```

---

## 🎮 Step 11: Run MiniOS

**Option A: Run in WSL (if QEMU GUI works)**

```bash
make run-carplay
```

**Option B: Run in MSYS2 (if WSL GUI doesn't work)**

1. **Build ISO in WSL** (already done above)
2. **Switch to MSYS2 terminal**
3. **Run:**
```bash
cd /c/Users/Axel\ Castellanos/Downloads/test/virtualboxandqemu/minios
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -boot d
```

---

## 🎯 Complete Workflow Summary

### Building ISOs (WSL Ubuntu)
```bash
# Open: Ubuntu terminal
cd /mnt/c/Users/YOUR_USERNAME/path/to/minios
make clean
make iso-carplay
```

### Running QEMU (MSYS2 - if WSL GUI doesn't work)
```bash
# Open: MSYS2 MINGW64 terminal
cd /c/Users/YOUR_USERNAME/path/to/minios
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M -boot d
```

---

## 📝 Quick Reference

### Open Ubuntu Terminal

**Method 1:**
- Start Menu → Type "Ubuntu" → Click "Ubuntu"

**Method 2:**
```powershell
# In any PowerShell or CMD:
wsl
```

### Important Paths

| Windows | WSL |
|---------|-----|
| `C:\Users\Axel\Downloads` | `/mnt/c/Users/Axel/Downloads` |
| `D:\Projects` | `/mnt/d/Projects` |
| `C:\` | `/mnt/c/` |

### Common Commands

```bash
# Update Ubuntu
sudo apt update && sudo apt upgrade -y

# Navigate to Windows files
cd /mnt/c/Users/YOUR_USERNAME/

# Build MiniOS
cd /mnt/c/path/to/minios
make clean
make iso-carplay

# Exit Ubuntu
exit
```

---

## 🔍 Troubleshooting

### Issue 1: "wsl --install" fails

**Error:** "WSL is not available"

**Solution:**
1. Enable virtualization in BIOS
2. Run:
```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```
3. Restart
4. Try again: `wsl --install`

### Issue 2: Ubuntu doesn't launch after restart

**Solution:**
```powershell
# Open PowerShell and type:
wsl --install -d Ubuntu-22.04
```

**Or:** Open Microsoft Store → Search "Ubuntu 22.04" → Install

### Issue 3: QEMU GUI doesn't work in WSL

**This is common - WSL has limited GUI support**

**Solution:** Build in WSL, run in MSYS2
```bash
# In WSL:
make iso-carplay

# In MSYS2:
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M
```

### Issue 4: Permission denied

```bash
# Add your user to sudo group (already done during setup)
# Or just use sudo:
sudo make iso-carplay
```

### Issue 5: Can't find Windows files

```bash
# Your Windows C: drive is at:
ls /mnt/c/

# Your user folder:
ls /mnt/c/Users/

# List all mounts:
ls /mnt/
```

---

## ✅ Verification Checklist

After setup, verify everything works:

**In Ubuntu (WSL):**

```bash
# Check tools
gcc --version
nasm --version
make --version
qemu-system-x86_64 --version
grub-mkrescue --version

# Navigate to minios
cd /mnt/c/Users/YOUR_USERNAME/path/to/minios

# Verify files
ls
# Should see: Makefile, kernel/, build/, etc.

# Build
make clean
make iso-carplay

# Check ISO exists
ls -lh build/minios_carplay.iso
# Should show: ~5MB file
```

---

## 🎯 Full Installation Script

**Copy this entire block into PowerShell (as admin):**

```powershell
# Install WSL
wsl --install

# Restart
Restart-Computer
```

**After restart, in Ubuntu terminal:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install build tools
sudo apt install -y build-essential nasm make qemu-system-x86 grub-pc-bin grub-common xorriso

# Navigate to minios (adjust path!)
cd /mnt/c/Users/YOUR_USERNAME/path/to/minios

# Build
make clean && make iso-carplay

# Run (if GUI works)
make run-carplay

# Or copy ISO path and run in MSYS2 QEMU
```

---

## 💡 Best Practices

### File Organization

**Recommended:** Keep source files on Windows drive
```
C:\Users\Axel\Downloads\test\virtualboxandqemu\minios\
```

**Access from both:**
- WSL: `/mnt/c/Users/Axel/Downloads/test/virtualboxandqemu/minios/`
- MSYS2: `/c/Users/Axel/Downloads/test/virtualboxandqemu/minios/`
- Windows: `C:\Users\Axel\Downloads\test\virtualboxandqemu\minios\`

### Workflow

1. **Edit code:** Windows (VS Code, Notepad++, etc.)
2. **Build ISO:** WSL Ubuntu (has GRUB)
3. **Run QEMU:** MSYS2 (faster GUI) or WSL

---

## 🎉 Done!

After following these steps, you'll have:

✅ Ubuntu running on Windows (WSL)
✅ All build tools installed (GCC, NASM, GRUB, QEMU)
✅ Can build MiniOS ISOs
✅ Can access Windows files from Ubuntu
✅ Can run QEMU in WSL or MSYS2

**You're ready to build and run MiniOS!** 🚀

---

## 📞 Quick Commands

**Open Ubuntu:**
```
Start Menu → Ubuntu
```

**Build MiniOS:**
```bash
cd /mnt/c/Users/YOUR_USERNAME/path/to/minios
make clean
make iso-carplay
```

**Run MiniOS:**
```bash
# In WSL (if GUI works):
make run-carplay

# In MSYS2 (if WSL GUI doesn't work):
qemu-system-x86_64 -cdrom build/minios_carplay.iso -m 256M
```

---

**Start with Step 1: Open PowerShell as Administrator!** 🎯
