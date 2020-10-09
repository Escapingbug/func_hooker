#ifndef VARS_H
#define VARS_H

/*
For hooking libc, we need a variable symbol to get the libc base.
With this, we are able to direct jmp to offset to avoid dlsym (which in turn uses libc itself)
*/
extern void* _IO_2_1_stdout_;

static __thread void* saved_reg1; /* usually saving rax, eax .. */
static __thread void* saved_stack;
static __thread void* jump_target; /* usually where to jump */
static __thread long custom_stack[0x1000]; /* care for what you can do with such low custom stack */
static __thread long custom_stack_top[0x20];

#endif