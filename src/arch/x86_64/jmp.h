#ifndef JMP_H
#ifdef __x86_64__
#define JMP_H

#include "vars.h"

#define PREPARE_LIBC_BASE(stdout_offset) asm( \
    "movq %%rax, %0\n" \
    "movq %1, %%rax\n" \
    "subq %3, %%rax\n" \
    "movq %%rax, %2\n" \
    "movq %0, %%rax\n" \
    :: "m"(saved_reg1), "m"(_IO_2_1_stdout_), "m"(jump_target), "i"(stdout_offset) \
);

#define JMP_OFFSET(offset) asm( \
    "movq %%rax, %0\n" \
    "movq %1, %%rax\n" /* libc base */ \
    "addq %2, %%rax\n" \
    "movq %%rax, %1\n" \
    "movq %0, %%rax\n" \
    "jmp *%1\n" \
    : \
    : "m"(saved_reg1), "m"(jump_target), "i"(offset) \
);

#define JMP_VAR(var) asm( \
    "jmp *%0\n" \
    : \
    : "r"(var) \
);


#endif
#endif