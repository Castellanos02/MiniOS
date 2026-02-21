/* linker_multiboot.ld - Linker script for multiboot kernel */

ENTRY(_start)
OUTPUT_FORMAT(elf32-i386)

SECTIONS
{
    /* Kernel starts at 1MB */
    . = 0x00100000;

    /* Multiboot header must be first */
    .multiboot : ALIGN(4K)
    {
        *(.multiboot)
    }

    /* Code */
    .text : ALIGN(4K)
    {
        *(.text)
        *(.text.*)
    }

    /* Read-only data */
    .rodata : ALIGN(4K)
    {
        *(.rodata)
        *(.rodata.*)
    }

    /* Initialized data */
    .data : ALIGN(4K)
    {
        *(.data)
        *(.data.*)
    }

    /* Uninitialized data (BSS) */
    .bss : ALIGN(4K)
    {
        *(COMMON)
        *(.bss)
        *(.bss.*)
    }
}
