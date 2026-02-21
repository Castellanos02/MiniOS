; multiboot_header.asm - Multiboot specification header for GRUB
; This allows GRUB to load our kernel

BITS 32

; Multiboot constants
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
    resb 16384  ; 16 KB stack
stack_top:

section .text
global _start
extern kernel_main

_start:
    ; GRUB has loaded us in 32-bit protected mode
    ; Set up stack
    mov esp, stack_top
    
    ; Push multiboot info (GRUB provides this)
    push ebx    ; Multiboot info structure
    push eax    ; Multiboot magic number
    
    ; Call the kernel
    call kernel_main
    
    ; If kernel returns (shouldn't happen), halt
.hang:
    cli
    hlt
    jmp .hang
