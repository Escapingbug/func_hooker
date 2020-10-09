import sys
import os.path
from elftools.elf.elffile import ELFFile
from subprocess import check_output

SOURCE_HEADER = r'''
#include "jmp.h"
#include "hook.h"
#include "pivot.h"
'''

AVOID_FUNCS = set([
    # These two are generated by compiler, and we don't really need to have it
    '_init',
    '_fini'
])


class Function:
    def __init__(self, name, offset):
        if '@' in name:
            # xxxx@glibc2.2.5
            name = name.split('@')[0]
        self.name = name
        self.offset = offset

    def is_libc_func(self):
        return self.offset != 0

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return '<Function({}, {})>'.format(self.name, self.offset)

    def __eq__(self, other):
        return hash(self) == hash(other)


class Binary:

    SOURCE_TEMPLATE_LIBC = r'''
/* unhooked version */
__attribute__((naked)) void unhooked_{name}() {{
    PREPARE_LIBC_BASE({stdout_offset})
    JMP_OFFSET({offset})
}}

/* hooked */
__attribute__((naked)) void {name}() {{
    PREPARE_LIBC_BASE({stdout_offset})
    PIVOT

    hooked_func("{name}");

    PIVOT_RECOVER
    JMP_OFFSET({offset})
}}
'''
    SOURCE_TEMPLATE_NORMAL = r'''
/* unhooked version */
__attribute__((naked)) void unhooked_{name}() {{
    PIVOT
    void *func = dlsym(-1, "{name}");
    PIVOT_RECOVER
    JMP_VAR(func)
}}

/* hooked */
__attribute__((naked)) void {name}() {{
    PIVOT

    hooked_func("{name}");
    void *func = dlsym(-1, "{name}");

    PIVOT_RECOVER
    JMP_VAR(func)
}}
'''
    
    def __init__(self, bin_path, hook_libc=True):
        """
        Note that we also hook root binary symbol (binary itself)
        But actually, that symbol should have no use, so let it be.
        """
        if type(bin_path) is bytes:
            bin_path = bin_path.decode('UTF-8')
        self.path = bin_path
        self.hook_libc = hook_libc
        self.f = open(bin_path, 'rb')
        self.elf = ELFFile(self.f)
        self.sections = list(self.elf.iter_sections())
        self.sym_sections = list(filter(lambda x: hasattr(x, 'iter_symbols'), self.sections))
        self.func_names = self._func_names()
        self.funcs = self._funcs()
        self.deps = []
        self._discover_deps()
        if hook_libc:
            self.stdout_offset = self._discover_stdout_offset()

    def _discover_stdout_offset(self):
        for dep in self.deps:
            if dep.is_libc():
                return dep.offset_of('_IO_2_1_stdout_')
            else:
                return dep._discover_stdout_offset()
        return None
                
    def _func_names(self):
        func_names = set()
        for sec in self.sym_sections:
            for sym in sec.iter_symbols():
                if 'st_info' in sym.entry:
                    if sym.entry.st_info['type'] == 'STT_FUNC':
                        func_names.add(sym.name)
        return func_names
            
    def is_libc(self):
        return os.path.basename(self.path) == 'libc.so.6'

    def _funcs(self):
        """
        returns:
            set of (name, offset). If not libc (which offset is not needed)
            then offset is 0
        """
        funcs = set()
        for sec in self.sym_sections:
            for sym in sec.iter_symbols():
                if 'st_info' in sym.entry:
                    if sym.entry.st_info['type'] == 'STT_FUNC':
                        if self.is_libc():
                            if not self.hook_libc:
                                continue
                            offset = sym.entry.st_value
                        else:
                            offset = 0
                        funcs.add(Function(sym.name, offset))
        return funcs

    def offset_of(self, sym_name):
        for sec in self.sym_sections:
            for sym in sec.iter_symbols():
                if sym.name == sym_name:
                    return sym.entry.st_value
    
    def _is_function(self, sym):
        if 'st_info' in sym.entry:
            return sym.entry['st_info']['type'] == 'STT_FUNC'
        else:
            return False

    def _discover_deps(self):
        dynamic_sec = self.elf.get_section_by_name('.dynamic')
        ldd_out = check_output(['ldd', self.path]).splitlines()
        lib_paths = {}
        for line in ldd_out:
            if not b'/' in line:
                continue

            if b'=>' in line:
                name, rest = line.split(b' => ')
                name = name.strip()
                path = rest.split(b' (')[0]
            else:
                path = line.split(b' (')[0].strip()
                name = os.path.basename(path)
                
            lib_paths[name] = path

        self.deps = []
        for tag in dynamic_sec.iter_tags():
            if hasattr(tag, 'needed'):
                self.deps.append(Binary(lib_paths[tag.needed.encode('UTF-8')], self.hook_libc))

    def all_funcs(self):
        # TODO: deal with collided symbols
        funcs = set()
        funcs.update(self._funcs())
        for dep in self.deps:
            funcs.update(dep.all_funcs())
        return funcs

    def close(self):
        self.f.close()

    def gen_source(self):
        funcs = self.all_funcs()
        gen_src = ''
        for f in funcs:
            if f in AVOID_FUNCS:
                continue
            if f.is_libc_func():
                if not self.stdout_offset:
                    raise Exception('cannot get libc base, no stdout offset found')
                gen_src += self.SOURCE_TEMPLATE_LIBC.format(
                    stdout_offset=self.stdout_offset,
                    name=f.name,
                    offset=f.offset
                )
            else:
                gen_src += self.SOURCE_TEMPLATE_NORMAL.format(
                    name=f.name
                )
        return gen_src

    def __str__(self):
        return '<Binary {}>'.format(repr(self.path))
        
def main():
    if len(sys.argv) != 4:
        print('Usage: {} bin hook_all_libc? output')
        return

    binary_path = sys.argv[1] 
    hook_libc = sys.argv[2] == "true"
    output = sys.argv[3]

    binary = Binary(binary_path, hook_libc) 
    src = binary.gen_source()

    with open(output, 'w') as f:
        f.write(SOURCE_HEADER + src)

if __name__ == '__main__':
    main()