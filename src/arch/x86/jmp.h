#ifndef JMP_OFFSET_H
#ifdef __i386__
#define JMP_OFFSET_H

#include "vars.h"

#define JMP_OFFSET(offset) asm( \
    "movl %%eax, saved_reg1@tpoff\n" \
    "movl %1, %%eax\n" /* libc base */ \
    "addl %2, %%eax\n" \
    "movl %%eax, %1\n" \
    "movl %0, %eax\n" \
    "jmp %1\n" \
    : \
    : "m"(saved_reg1), "m"(jump_target), "i"(offset) \
);

#endif
#endif