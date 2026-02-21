; test_kernel.asm - Minimal test kernel to verify boot process

BITS 64

global _start

section .text
_start:
    ; Write "KERNEL OK" to screen
    mov rax, 0xB8000
    mov word [rax], 0x0F4B     ; 'K'
    mov word [rax+2], 0x0F45   ; 'E'
    mov word [rax+4], 0x0F52   ; 'R'
    mov word [rax+6], 0x0F4E   ; 'N'
    mov word [rax+8], 0x0F45   ; 'E'
    mov word [rax+10], 0x0F4C  ; 'L'
    mov word [rax+12], 0x0F20  ; ' '
    mov word [rax+14], 0x0F4F  ; 'O'
    mov word [rax+16], 0x0F4B  ; 'K'
    
.hang:
    hlt
    jmp .hang
