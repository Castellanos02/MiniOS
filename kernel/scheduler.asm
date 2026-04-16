; scheduler.asm - Fixed-Priority Preemptive Scheduler (FPPS) for MiniOS
; BITS 32 — compiled for the iso-carplay target (elf32-i386 / multiboot)
;
; Exports:
;   switch_context(Task *prev, Task *next)  — context switch routine
;   isr_pit                                 — PIT IRQ0 interrupt handler (vector 0x20)
;
; Task struct layout (must match kernel_carplay.c):
;   offset  0: esp  (uint32_t)
;   offset  4: ebp  (uint32_t)
;   offset  8: state (uint32_t)
;   offset 12: priority (uint8_t)
;   offset 16: stack_top (uint32_t)
;   offset 20: wake_tick (uint32_t)

BITS 32

global switch_context
global isr_pit

extern scheduler_tick       ; C function called from isr_pit

%define TASK_ESP  0         ; byte offset of esp field in Task
%define TASK_EBP  4         ; byte offset of ebp field in Task

section .text

; -----------------------------------------------------------------------
; switch_context(Task *prev, Task *next)  [cdecl, 32-bit]
;
; Stack on entry (before push ebp):
;   [esp+0]  = return address
;   [esp+4]  = prev  (Task*)
;   [esp+8]  = next  (Task*)
;
; Saves the full register context of the calling (prev) task onto its own
; stack, stores the resulting ESP/EBP into prev->esp/ebp, then restores
; ESP/EBP from next->esp/ebp and unwinds the saved frame for the next task.
; -----------------------------------------------------------------------
switch_context:
    push ebp
    mov  ebp, esp               ; ebp now points to our frame

    ; ── Save prev task ──────────────────────────────────────────────────
    mov  eax, [ebp + 8]         ; eax = prev Task*

    pusha                       ; pushes EAX,ECX,EDX,EBX,ESP_snap,EBP,ESI,EDI (32 B)
    pushf                       ; pushes EFLAGS (4 B)
                                ; esp is now 36 bytes below where it was on entry

    mov  [eax + TASK_ESP], esp  ; prev->esp = current esp (below pushf/pusha)
    mov  [eax + TASK_EBP], ebp  ; prev->ebp = current ebp (our frame pointer)

    ; ── Restore next task ───────────────────────────────────────────────
    mov  eax, [ebp + 12]        ; eax = next Task*

    mov  esp, [eax + TASK_ESP]  ; load next task's saved stack pointer
    mov  ebp, [eax + TASK_EBP]  ; load next task's saved base pointer

    popf                        ; restore EFLAGS (enables interrupts if IF was set)
    popa                        ; restore EDI,ESI,EBP,skip-ESP,EBX,EDX,ECX,EAX

    pop  ebp                    ; restore the saved ebp from the frame we set up
    ret                         ; return into the next task's call site
                                ; (or into the task entry function for a new task)

; -----------------------------------------------------------------------
; isr_pit — PIT Channel 0 IRQ0 handler, IDT vector 0x20
;
; The CPU has already pushed EFLAGS, CS, EIP onto the interrupted task's
; stack before jumping here (standard protected-mode interrupt gate path).
; We save/restore all GP registers around the C scheduler_tick call.
;
; If scheduler_tick calls switch_context, the function returns on a
; *different* task's stack — the isr_pit epilogue (EOI + iret) still
; executes correctly because it's purely position-independent.
; -----------------------------------------------------------------------
isr_pit:
    pusha                       ; save all 8 GP registers (32 B)
    pushf                       ; save EFLAGS (4 B) — IF is already 0 (interrupt gate)

    call scheduler_tick         ; C function: increments g_tick, may call switch_context

    mov  al, 0x20
    out  0x20, al               ; send End-Of-Interrupt to master PIC (port 0x20)

    popf                        ; restore EFLAGS
    popa                        ; restore GP registers
    iret                        ; return: pops EIP, CS, EFLAGS from the interrupted frame
