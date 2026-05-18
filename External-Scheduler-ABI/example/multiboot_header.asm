; multiboot_header.asm — Multiboot 1 header + GRUB entry point.
;
; This file is YOURS to provide as the kernel's entry point. The
; scheduler library does not include or assume any particular boot
; protocol — this is just the canonical multiboot 1 / GRUB setup.

BITS 32

MULTIBOOT_MAGIC         equ 0x1BADB002
MULTIBOOT_PAGE_ALIGN    equ 1 << 0
MULTIBOOT_MEMORY_INFO   equ 1 << 1
MULTIBOOT_FLAGS         equ MULTIBOOT_PAGE_ALIGN | MULTIBOOT_MEMORY_INFO
MULTIBOOT_CHECKSUM      equ -(MULTIBOOT_MAGIC + MULTIBOOT_FLAGS)

section .multiboot
align 4
    dd MULTIBOOT_MAGIC
    dd MULTIBOOT_FLAGS
    dd MULTIBOOT_CHECKSUM

section .bss
align 16
stack_bottom:
    resb 16384          ; 16 KB bootstrap stack
stack_top:

section .text
global _start
extern kernel_main      ; <-- provided by minimal_kernel.c

_start:
    mov esp, stack_top  ; set up our bootstrap stack
    push ebx            ; pass multiboot info pointer  (2nd arg)
    push eax            ; pass multiboot magic number  (1st arg)
    call kernel_main
.hang:
    cli
    hlt
    jmp .hang
