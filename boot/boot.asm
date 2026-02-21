; Simple bootloader for x86_64
; Loads kernel and sets up long mode

BITS 16
ORG 0x7C00

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    ; Print boot message
    mov si, boot_msg
    call print_string

    ; Load kernel from disk
    mov ah, 0x02        ; Read sectors
    mov al, 50          ; Number of sectors to read
    mov ch, 0           ; Cylinder 0
    mov cl, 2           ; Sector 2 (after bootloader)
    mov dh, 0           ; Head 0
    mov bx, 0x1000      ; Destination
    int 0x13
    jc disk_error

    ; Enable A20 line
    call enable_a20

    ; Load GDT
    lgdt [gdt_descriptor]

    ; Enter protected mode
    mov eax, cr0
    or eax, 1
    mov cr0, eax

    ; Jump to protected mode code
    jmp CODE_SEG:protected_mode

disk_error:
    mov si, disk_err_msg
    call print_string
    hlt

print_string:
    lodsb
    or al, al
    jz .done
    mov ah, 0x0E
    int 0x10
    jmp print_string
.done:
    ret

enable_a20:
    in al, 0x92
    or al, 2
    out 0x92, al
    ret

BITS 32
protected_mode:
    ; Set up segments
    mov ax, DATA_SEG
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x90000

    ; Check for long mode support
    call check_long_mode
    
    ; Set up paging for long mode
    call setup_paging

    ; Load GDT64
    lgdt [gdt64_descriptor]

    ; Enable long mode
    mov ecx, 0xC0000080
    rdmsr
    or eax, 1 << 8
    wrmsr

    ; Enable paging
    mov eax, cr0
    or eax, 1 << 31
    mov cr0, eax

    ; Jump to long mode
    jmp CODE64_SEG:long_mode

check_long_mode:
    mov eax, 0x80000000
    cpuid
    cmp eax, 0x80000001
    jb .no_long_mode
    mov eax, 0x80000001
    cpuid
    test edx, 1 << 29
    jz .no_long_mode
    ret
.no_long_mode:
    hlt

setup_paging:
    ; Clear page tables
    mov edi, 0x70000
    mov cr3, edi
    xor eax, eax
    mov ecx, 0x4000
    rep stosd
    mov edi, 0x70000

    ; Set up PML4
    mov dword [edi], 0x71003
    add edi, 0x1000
    
    ; Set up PDPT
    mov dword [edi], 0x72003
    add edi, 0x1000
    
    ; Set up PD (identity map first 2MB)
    mov dword [edi], 0x000083
    mov dword [edi + 8], 0x200083
    
    ret

BITS 64
long_mode:
    ; Set up segments for long mode
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    
    ; Set up stack
    mov rsp, 0x90000
    
    ; Clear screen
    mov rdi, 0xB8000
    mov rcx, 80*25
    mov ax, 0x0F20
    rep stosw
    
    ; Print success message
    mov rdi, 0xB8000
    mov rsi, long_mode_msg
    mov ah, 0x0F
.print_loop:
    lodsb
    test al, al
    jz .done_print
    stosw
    jmp .print_loop
.done_print:
    
    ; Jump to kernel at 0x1000
    mov rax, 0x1000
    jmp rax

long_mode_msg db 'Long mode OK, loading kernel...', 0

; GDT for protected mode
gdt_start:
    dq 0                ; Null descriptor
gdt_code:
    dw 0xFFFF           ; Limit
    dw 0                ; Base (low)
    db 0                ; Base (middle)
    db 10011010b        ; Access
    db 11001111b        ; Flags + Limit
    db 0                ; Base (high)
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

; GDT for long mode
gdt64_start:
    dq 0
gdt64_code:
    dq 0x00209A0000000000
gdt64_data:
    dq 0x0000920000000000
gdt64_end:

gdt64_descriptor:
    dw gdt64_end - gdt64_start - 1
    dq gdt64_start

CODE_SEG equ gdt_code - gdt_start
DATA_SEG equ gdt_data - gdt_start
CODE64_SEG equ gdt64_code - gdt64_start

boot_msg db 'MiniOS Booting...', 13, 10, 0
disk_err_msg db 'Disk Error!', 13, 10, 0

times 510-($-$$) db 0
dw 0xAA55
