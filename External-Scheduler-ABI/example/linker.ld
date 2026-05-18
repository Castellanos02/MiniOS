/* linker.ld — Minimal multiboot linker script.
 *
 * You provide this. The scheduler doesn't care about layout; it only
 * needs ELF32 i386 output that GRUB will load above 1 MB.
 */

ENTRY(_start)
OUTPUT_FORMAT(elf32-i386)

SECTIONS
{
    . = 0x00100000;     /* Kernel starts at 1 MB */

    .multiboot : ALIGN(4K) { *(.multiboot) }
    .text      : ALIGN(4K) { *(.text)   *(.text.*) }
    .rodata    : ALIGN(4K) { *(.rodata) *(.rodata.*) }
    .data      : ALIGN(4K) { *(.data)   *(.data.*) }
    .bss       : ALIGN(4K) { *(COMMON) *(.bss) *(.bss.*) }
}
