project('func_hooker', 'c')

prog_python = import('python').find_installation('python3')
if get_option('hook_libc')
    hook_libc_str = 'true'
else
    hook_libc_str = 'false'
endif
hooking_funcs = custom_target(
    'hooking.c',
    output : ['hooking.c'],
    input : get_option('hook_binary'),
    command : [prog_python, join_paths(meson.source_root(), 'scripts', 'gen.py'), '@INPUT@', hook_libc_str, '@OUTPUT@']
)

get_arch_path = join_paths(meson.source_root(), 'scripts', 'get_arch.py')
arch = run_command(prog_python, get_arch_path, get_option('hook_binary')).stdout().strip()

x86_include_directory = include_directories(join_paths('src', 'arch', 'x86'))
x86_64_include_directory = include_directories(join_paths('src', 'arch', 'x86_64'))
include_dir = 0
if arch == 'x86'
    add_global_arguments('-m32', language : 'c')
    include_dir = x86_include_directory
elif arch == 'x86_64'
    include_dir = x86_64_include_directory
endif

shared_module('hook', ['hook/hook.c', hooking_funcs], include_directories : [include_dir, join_paths('src'), join_paths('src', 'arch')])