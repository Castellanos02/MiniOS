; kernel_entry.asm - Kernel entry point
; This is the first code that runs when the bootloader jumps to the kernel

BITS 64

global _start
extern kernel_main

section .text
_start:
    ; Clear direction flag
    cld
    
    ; Set up stack (bootloader should have done this, but be safe)
    mov rsp, 0x90000
    
    ; Clear all general purpose registers
    xor rax, rax
    xor rbx, rbx
    xor rcx, rcx
    xor rdx, rdx
    xor rsi, rsi
    xor rdi, rdi
    xor rbp, rbp
    xor r8, r8
    xor r9, r9
    xor r10, r10
    xor r11, r11
    xor r12, r12
    xor r13, r13
    xor r14, r14
    xor r15, r15
    
    ; Call the C kernel
    call kernel_main
    
    ; If kernel_main returns (it shouldn't), halt
.hang:
    cli
    hlt
    jmp .hang
