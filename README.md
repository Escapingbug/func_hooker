# func hooker

requires:

- gcc-8 : why? because "naked" is only implemented in gcc 8 for x86 and x86_64 (how come?!)

# Usage

Write your code (.c) under hook directory, and let meson build this. Finally, use `LD_PRELOAD` to load your compiled artifact.