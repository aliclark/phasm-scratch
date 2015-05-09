
import re

# FIXME: depends on builtin_signed

######## COMMON API ##########

E_INTEGER = 'INT'
E_STRING  = 'STR'
E_BIN_RAW = 'RAW'
E_BLOCK   = 'BLK'
E_BUILTIN_FUNC = 'BUILTIN'
E_NEEDS_WORK   = 'NEEDS_WORK'

def e_needs_work(length=None):
    return {'len': length, 'final': False, 'type':E_NEEDS_WORK, 'data': None}

def e_integer(n):
    return {'len': None, 'final': True, 'type':E_INTEGER, 'data':n}

def e_bin_raw(bitlen, x):
    return {'len':bitlen, 'final': True, 'type':E_BIN_RAW, 'data': x}

def e_block(assignments, value, labels=None):
    if not labels:
        labels = {}
    return {'len': value['len'], 'final': value['final'], 'type':E_BLOCK,
            'data': {'vars':assignments, 'val':value, 'labels':labels}}

def e_builtin_func(paramsnum, f):
    return {'len': None, 'final': True, 'type':E_BUILTIN_FUNC,
            'data': {'paramsnum': paramsnum, 'func': f}}

######## / COMMON API ##########

################################
# Yuck! Copy-pasta'd from bin.py
#
# It would be nice to make this an abstract module that is able to
# evaluate other code to call bin.s in a normal way.

# Like U, but handles negative numbers with 2's complement
def builtin_signed(ix, jx):
    if not ix['final']:
        return e_needs_work()
    if not jx['final']:
        return e_needs_work(ix['data'])
    if ix['type'] != E_INTEGER or jx['type'] != E_INTEGER:
        raise Exception("S takes Integer, Integer arguments, got " + str(ix) + ", " + str(jx))
    if ix['data'] < 0:
        raise Exception("Bitsize must be non-negative")

    if jx['data'] >= 2**((ix['data']*8)-1):
        raise Exception("Argument is too big for the space")
    if jx['data'] <  -1 * (2**((ix['data']*8)-1)):
        raise Exception("Argument is too negative for the space, " + str(jx))

    num = jx['data']

    if num < 0:
        num = (1 << ix['data']*8) + num

    out = []
    bytes_rem = ix['data']
    bs = hex(num)[2:]

    if len(bs) % 2 != 0:
        bs = '0' + bs
    for i in reversed(range(0, len(bs), 2)):
        byt = int(bs[i:i+2], 16)
        out.append(byt)
        bytes_rem -= 1

    while bytes_rem > 0:
        out.append(0)
        bytes_rem -= 1

    return e_bin_raw(ix['data'], out)

######## / YUCK ##########

nop = 0x90

mov_reg = {
    'rax': 0xb8,
    'rcx': 0xb9,
    'rdx': 0xba,
    'rbx': 0xbb,
}

rbp_arg = re.compile(r'\[rbp\+(?P<mul>[0-9]+)\]')

rbp_dst_reg = {
    'rcx': 0x4d,
    'rdx': 0x55,
    'rsi': 0x75,
    'rdi': 0x7d,
}

def builtin_mov(dx, sx):
    if not dx['final'] or not sx['final']:
        return e_needs_work(5)

    if dx['type'] == E_STRING and sx['type'] == E_STRING:
        if dx['data'] == 'rbp' and sx['data'] == 'rsp':
            return e_bin_raw(5, [0x48, 0x89, 0xe5, nop, nop])
        if dx['data'] == 'rsp' and sx['data'] == 'rbp':
            return e_bin_raw(5, [0x48, 0x89, 0xec, nop, nop])

        m = rbp_arg.match(sx['data'])
        if m:
            start = [0x48, 0x8b]
            if dx['data'] not in rbp_dst_reg:
                raise Exception("Unknown rbp offset dest reg")
            if m.group('mul') in ('16', '24'):
                mul = int(m.group('mul'))
            else:
                raise Exception("Unknown rbp offset mul")
            return e_bin_raw(4, start + [rbp_dst_reg[dx['data']], mul])

    if dx['type'] == E_STRING and sx['type'] == E_INTEGER:
        src = builtin_signed(e_integer(4), sx)
        if dx['data'] not in mov_reg:
            raise Exception("Unknown mov register " + str(dx))
        return e_bin_raw(5, [mov_reg[dx['data']]] + src['data'])

    raise Exception("Unknown mov type")

push_reg = {
    'rax': 0x50,
    'rcx': 0x51,
    'rdx': 0x52,
    'rbx': 0x53,

    'rbp': 0x55,
    'rsi': 0x56,
    'rdi': 0x57,
}

def builtin_push(sx):
    if not sx['final']:
        return e_needs_work(5)

    if sx['type'] == E_STRING:
        if sx['data'] not in push_reg:
            raise Exception("Unknown push register " + str(sx))
        return e_bin_raw(5, [push_reg[sx['data']], nop, nop, nop, nop])

    if sx['type'] == E_INTEGER:
        if sx['data'] < -128 or sx['data'] > 127:
            src = builtin_signed(e_integer(4), sx)
            return e_bin_raw(5, [0x68] + src['data'])
        else:
            src = builtin_signed(e_integer(1), sx)
            return e_bin_raw(5, [0x6a] + src['data'] + [nop, nop, nop])

    raise Exception("Unknown push type")

pop_reg = {
    'rax': 0x58,
    'rcx': 0x59,
    'rdx': 0x5a,
    'rbx': 0x5b,

    'rbp': 0x5d,
    'rsi': 0x5e,
    'rdi': 0x5f,
}

def builtin_pop(dx):
    if not dx['final']:
        return e_needs_work(1)

    if dx['type'] == E_STRING:
        if dx['data'] not in pop_reg:
            raise Exception("Unknown pop register " + str(dx))
        return e_bin_raw(1, [pop_reg[dx['data']]])

    raise Exception("Unknown pop type")

builtins_asm = e_block([
    ('mov', e_builtin_func(2, builtin_mov)),
    ('push', e_builtin_func(1, builtin_push)),
    ('pop', e_builtin_func(1, builtin_pop)),
],
                       e_bin_raw(0, []))

# perhaps build() could return a function that itself takes modules as
# arguments?
#
# This might not actually be a good idea because we'd be unable to do
# anything with non-builtin functions given the lack of an evaluator.
#
# Perhaps we should accept an evaluator as an argument and return an
# object that may or may not use the evaluator internally?

def build():
    return builtins_asm
