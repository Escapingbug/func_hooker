#ifndef PIVOT_H
#ifdef __x86_64__
#define PIVOT_H

#include "vars.h"

#define PIVOT \
asm( \
    "movq %%rsp, %0\n" \
    "movq %1, %%rsp\n" \
    ::"m"(saved_stack), "m"(custom_stack_top) \
);

#define PIVOT_RECOVER \
asm( \
    "movq %0, %%rsp\n" \
    ::"m"(saved_stack) \
);

#endif
#endif