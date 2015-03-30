
from common import *

def mov_common(reg, sx):
    if not sx['final']:
        return e_needs_work(1 + sx['len'])
    if sx['type'] != E_BIN_RAW:
        raise Exception("mov takes bin, got " + str(sx))
    return e_bin_raw(1+sx['len'], [reg] + sx['data'])

def mov_eax(var):
    return mov_common(0xb8, var)
def mov_ecx(var):
    return mov_common(0xb9, var)
def mov_edx(var):
    return mov_common(0xba, var)
def mov_ebx(var):
    return mov_common(0xbb, var)

def push_rax():
    return e_bin_raw(1, [0x50])
def pop_rax():
    return e_bin_raw(1, [0x58])

def cmp_eax_1b(bx):
    i = bx['data']
    return e_bin_raw(3, [0x83, 0xF8, i])

def add_eax_1b(bx):
    i = bx['data']
    return e_bin_raw(3, [0x83, 0xC0, i])

def jump_1b_common(op, cur, dest):
    if not cur['final'] or not dest['final']:
        return e_needs_work(2)

    if cur['type'] != E_INTEGER or dest['type'] != E_INTEGER:
        raise Exception("jge takes Integer, Integer")

    rel = dest['data'] - cur['data']

    if rel > 0xFF:
        raise Exception("dest is too far ahead")
    if rel < 0:
        rel = 0x100 + rel
    if rel > 0xFF:
        raise Exception("dest is too far behind")

    return e_bin_raw(2, [op, rel])

def jge_1b(cur, dest):
    return jump_1b_common(0x7D, cur, dest)

def jmp_1b(cur, dest):
    return jump_1b_common(0xEB, cur, dest)

builtins_std = e_block([
    ('mov_eax', e_builtin_func(1, mov_eax)),
    ('mov_ecx', e_builtin_func(1, mov_ecx)),
    ('mov_edx', e_builtin_func(1, mov_edx)),
    ('mov_ebx', e_builtin_func(1, mov_ebx)),
    ('mov_reg1', e_builtin_func(1, mov_eax)),
    ('push_rax', e_builtin_func(0, push_rax)),
    ('pop_rax', e_builtin_func(0, pop_rax)),
    ('cmp_eax_1b', e_builtin_func(1, cmp_eax_1b)),
    ('add_eax_1b', e_builtin_func(1, add_eax_1b)),
    ('jge_1b', e_builtin_func(2, jge_1b)),
    ('jmp_1b', e_builtin_func(2, jmp_1b)),
],
                       e_bin_concat([]))

def build():
    return builtins_std
