; minimal_boot.asm - Ultra-minimal bootloader for testing
; This bootloader just prints messages at each stage to see where it fails

BITS 16
ORG 0x7C00

start:
    ; Disable interrupts
    cli
    
    ; Set up segments
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    
    ; Re-enable interrupts
    sti
    
    ; Print "1"
    mov al, '1'
    call print_char
    
    ; Enable A20 (simple method)
    in al, 0x92
    or al, 2
    out 0x92, al
    
    ; Print "2"
    mov al, '2'
    call print_char
    
    ; Load GDT
    lgdt [gdt_descriptor]
    
    ; Print "3"
    mov al, '3'
    call print_char
    
    ; Enter protected mode
    mov eax, cr0
    or eax, 1
    mov cr0, eax
    
    ; Far jump to protected mode
    jmp 0x08:protected_mode

print_char:
    mov ah, 0x0E
    mov bh, 0
    int 0x10
    ret

; GDT
gdt_start:
    dq 0                    ; Null descriptor
gdt_code:
    dw 0xFFFF              ; Limit
    dw 0                   ; Base (low)
    db 0                   ; Base (middle)
    db 10011010b           ; Access
    db 11001111b           ; Flags + Limit
    db 0                   ; Base (high)
gdt_data:
    dw 0xFFFF
    dw 0
    db 0
    db 10010010b
    db 11001111b
    db 0
gdt_end:

gdt_descriptor:
    dw gdt_end - gdt_start - 1
    dd gdt_start

BITS 32
protected_mode:
    ; Set up segments
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x90000
    
    ; Write "4" to screen (VGA text mode)
    mov byte [0xB8000], '4'
    mov byte [0xB8001], 0x0F
    
    ; Write "PROT" to show we're in protected mode
    mov dword [0xB8002], 0x0F520F4F  ; 'OR'
    mov dword [0xB8006], 0x0F540F54  ; 'TT'
    
    ; Halt
.hang:
    hlt
    jmp .hang

times 510-($-$$) db 0
dw 0xAA55
