# Example Makefile — builds a tiny multiboot kernel that uses the
# standalone scheduler library. Adapt paths and flags for your project.
#
#   make kernel    -> example_kernel.bin
#   make iso       -> example_kernel.iso  (needs GRUB + xorriso)
#   make run       -> boots iso in QEMU
#   make clean

# ---- toolchain ----
CC      ?= gcc
AS      ?= nasm
LD      ?= ld

# ---- paths ----
SCHED   := ..
BUILD   := build

# ---- flags ----
CFLAGS  := -m32 -ffreestanding -fno-stack-protector -nostdlib -I$(SCHED)
LDFLAGS := -m elf_i386 -T linker.ld -nostdlib

# ---- targets ----
OBJS := \
	$(BUILD)/multiboot_header.o \
	$(BUILD)/scheduler_asm.o    \
	$(BUILD)/scheduler.o        \
	$(BUILD)/minimal_kernel.o

all: kernel

$(BUILD):
	mkdir -p $@

$(BUILD)/multiboot_header.o: multiboot_header.asm | $(BUILD)
	$(AS) -f elf32 $< -o $@

$(BUILD)/scheduler_asm.o: $(SCHED)/scheduler.asm | $(BUILD)
	$(AS) -f elf32 $< -o $@

$(BUILD)/scheduler.o: $(SCHED)/scheduler.c $(SCHED)/scheduler.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/minimal_kernel.o: minimal_kernel.c $(SCHED)/scheduler.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

kernel: $(BUILD)/example_kernel.bin

$(BUILD)/example_kernel.bin: $(OBJS) linker.ld
	$(LD) $(LDFLAGS) $(OBJS) -o $@
	@echo "✓ Built $@"

iso: $(BUILD)/example_kernel.iso

$(BUILD)/example_kernel.iso: $(BUILD)/example_kernel.bin
	mkdir -p $(BUILD)/isodir/boot/grub
	cp $(BUILD)/example_kernel.bin $(BUILD)/isodir/boot/kernel.bin
	printf 'set timeout=0\nset default=0\nmenuentry "example" {\n  multiboot /boot/kernel.bin\n  boot\n}\n' \
		> $(BUILD)/isodir/boot/grub/grub.cfg
	grub-mkrescue -o $@ $(BUILD)/isodir
	@echo "✓ Built $@"

run: $(BUILD)/example_kernel.iso
	qemu-system-x86_64 -cdrom $< -m 256M -boot d

clean:
	rm -rf $(BUILD)

.PHONY: all kernel iso run clean
