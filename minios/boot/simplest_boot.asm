; simplest_boot.asm - Absolutely minimal bootloader
; Just prints "OK" and halts - no mode changes, no nothing

BITS 16
ORG 0x7C00

start:
    ; Set up segment
    mov ax, 0x07C0
    mov ds, ax
    
    ; Print 'O'
    mov ah, 0x0E
    mov al, 'O'
    int 0x10
    
    ; Print 'K'
    mov al, 'K'
    int 0x10
    
    ; Print '!'
    mov al, '!'
    int 0x10
    
    ; Halt forever
.hang:
    hlt
    jmp .hang

times 510-($-$$) db 0
dw 0xAA55
