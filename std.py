
import re
import string




######## COMMON API ##########

E_INTEGER = 'INT'
E_STRING  = 'STR'
E_LAMBDA  = 'LAM'
E_VARREF  = 'VAR'

E_APPLICATION = 'APP'

E_OFFSET_LABEL = 'OFF'

E_OFFSET_REF = 'OFFREF'

E_BIN_RAW = 'RAW'
E_BIN_CONCAT = 'BINCAT'

E_BLOCK = 'BLK'

E_BUILTIN_FUNC = 'BUILTIN'

E_NEEDS_WORK = 'NEEDS_WORK'


def getbin(sx):
    if sx['type'] == E_BIN_RAW:
        return sx

    if sx['type'] == E_BIN_CONCAT:
        out = []
        for x in sx['data']:
            b = getbin(x)
            if b['type'] != E_BIN_RAW:
                raise Exception("Expected bin: " + str(b))
            out.append(b)
        sumlen = 0
        joined = []
        if out:
            sumlen = reduce(lambda x, y: x + y, [x['len'] for x in out])
            joined = reduce(lambda x, y: x + y, [x['data'] for x in out])
        return e_bin_raw(sumlen, joined)

    if sx['type'] == E_OFFSET_LABEL:
        return e_bin_raw(0, [])

    raise ValueError("Tried to get binary from " + str(sx))


# final: whether this is in its final form
# len:   the length of binary content, or None if n/a / unknown

# An easy way to tell the caller we need to be reconstructed (instead
# of having to reconstruct ourselves). This concept is possibly a bad
# idea.
def e_needs_work(length=None):
    return {'len': length, 'final': False, 'type':E_NEEDS_WORK, 'data': None}

def e_integer(n):
    return {'len': None, 'final': True, 'type':E_INTEGER, 'data':n}

def e_string(n):
    return {'len': None, 'final': True, 'type':E_STRING, 'data':n}

def e_varref(x):
    return {'len': None, 'final': False, 'type':E_VARREF, 'data': x}

def e_offset_label(x):
    return {'len': 0, 'final': True, 'type':E_OFFSET_LABEL, 'data': x}

def e_offset_ref(x):
    return {'len': None, 'final': False, 'type':E_OFFSET_REF, 'data': x}

def get_bin_concat_len(lst):
    lens = [x['len'] for x in lst]
    if not any([l is None for l in lens]):
        return sum(lens)
    return None

def e_bin_concat(lst, labels=None):
    if not labels:
        labels = {}
    return {'len': get_bin_concat_len(lst), 'final': all([x['final'] for x in lst]),
            'type':E_BIN_CONCAT, 'data': lst}

# x is a list of integers
def e_bin_raw(bitlen, x):
    return {'len':bitlen, 'final': True, 'type':E_BIN_RAW, 'data': x}

def e_block(assignments, value, labels=None):
    if not labels:
        labels = {}
    return {'len': value['len'], 'final': value['final'], 'type':E_BLOCK,
            'data': {'vars':assignments, 'val':value, 'labels':labels}}

def e_application(f, args, env=None):
    if f['type'] != E_VARREF:
        raise Exception("Application can only be performed on named functions")
    return {'len': None, 'final': False, 'type':E_APPLICATION, 'data': {'f': f, 'args': args, 'env':env}}

def e_lambda(params, body, env=None):
    return {'len': None, 'final': True, 'type':E_LAMBDA, 'data': {'params':params, 'body':body, 'env':env}}

def e_builtin_func(paramsnum, f):
    return {'len': None, 'final': True, 'type':E_BUILTIN_FUNC,
            'data': {'paramsnum': paramsnum, 'func': f}}

######## / COMMON API ##########





# Builtin Functions - the args are already evaluated and if they were
# blocks with vars then just the value part is used.

def generic_python_encode(ix, sx, charset):
    if not ix['final']:
        return e_needs_work()
    if not sx['final']:
        return e_needs_work(ix['data'])
    if ix['type'] != E_INTEGER:
        raise Exception(charset + " takes Integer as first argument")
    if sx['type'] != E_STRING:
        raise Exception(charset + " takes String as second argument")
    b = [ord(x) for x in sx['data'].encode(charset)]
    bitlen = len(b)
    if ix['data'] != bitlen:
        raise Exception(charset + " size was invalid")
    return e_bin_raw(bitlen, b)

def generic_python_length(sx, charset):
    if not sx['final']:
        return e_needs_work()
    if sx['type'] != E_STRING:
        raise Exception(charset + " takes String as second argument")
    b = sx['data'].encode(charset)
    bitlen = len(b)
    return e_integer(bitlen)

def builtin_Ascii(ix, sx):
    return generic_python_encode(ix, sx, 'ascii')

def builtin_AsciiLength(sx):
    return generic_python_length(sx, 'ascii')

def builtin_Utf8(ix, sx):
    return generic_python_encode(ix, sx, 'utf8')

def builtin_Utf8Length(sx):
    return generic_python_length(sx, 'utf8')


def builtin_Bin(ix, sx):
    if not ix['final']:
        return e_needs_work()
    if not sx['final']:
        return e_needs_work(ix['data'])

    if ix['type'] != E_INTEGER:
        raise Exception("Bin takes Integer as first argument")

    if sx['type'] == E_BIN_RAW:
        if sx['len'] != ix['data']:
            raise Exception("Expected length "+str(ix['data'])+
                            " did not match result: " + sx['data'])
        return sx

    if sx['type'] == E_BIN_CONCAT:
        if not all(x['final'] for x in sx['data']):
            return e_needs_work(get_bin_concat_len(sx['data']))
        if sx['len'] != ix['data']:
            raise Exception("Expected length "+str(ix['data'])+
                            " did not match result: " + sx['data'])
        rv = getbin(sx)
        if sx['len'] != rv['len']:
            raise Exception('length changed?!')
        return rv

    if sx['type'] != E_STRING:
        raise Exception("Bin takes String as second argument, got " + str(sx['type']))

    bs = sx['data'].replace(' ', '').replace('\t', '').replace('\r', '').replace('\n', '')
    for ch in bs:
        if ch not in string.hexdigits:
            raise Exception("Expected hex but saw: " + ch)

    if len(bs) % 2 != 0:
        raise Exception("Bin only possible for full bytes")

    bitlen = len(bs) / 2
    if ix['data'] != bitlen:
        raise Exception("Expected length "+str(ix['data'])+" did not match result: " + sx['data'])

    out = []
    for i in range(0, len(bs), 2):
        byt = int(bs[i:i+2], 16)
        out.append(byt)

    return e_bin_raw(bitlen, out)

# other functions will do truncation, 2's complement and big endian in
# future
def builtin_U(ix, jx):
    if not ix['final']:
        return e_needs_work()
    if not jx['final']:
        return e_needs_work(ix['data'])
    if ix['type'] != E_INTEGER or jx['type'] != E_INTEGER:
        raise Exception("U takes Integer, Integer arguments, got " + str(ix) + ", " + str(jx))
    if ix['data'] < 0:
        raise Exception("Bitsize must be non-negative")
    if jx['data'] < 0:
        raise Exception("Argument must be non-negative")
    if jx['data'] >= 2**(ix['data']*8):
        raise Exception("Argument is too big for the space")

    out = []
    bytes_rem = ix['data']
    bs = hex(jx['data'])[2:]
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

# Like U, but handles negative numbers with 2's complement
def builtin_S(ix, jx):
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

def builtin_Multiply(ix, jx):
    if not ix['final'] or not jx['final']:
        return e_needs_work()
    if ix['type'] != E_INTEGER or jx['type'] != E_INTEGER:
        raise Exception("Multiply takes Integer, Integer arguments")
    return e_integer(ix['data'] * jx['data'])

def builtin_Add(ix, jx):
    if not ix['final'] or not jx['final']:
        return e_needs_work()
    if ix['type'] != E_INTEGER or jx['type'] != E_INTEGER:
        raise Exception("Add takes Integer, Integer arguments")
    return e_integer(ix['data'] + jx['data'])

def builtin_Subtract(ix, jx):
    if not ix['final'] or not jx['final']:
        return e_needs_work()
    if ix['type'] != E_INTEGER or jx['type'] != E_INTEGER:
        raise Exception("Subtract takes Integer, Integer arguments")
    return e_integer(ix['data'] - jx['data'])

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
        src = builtin_S(e_integer(4), sx)
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
            src = builtin_S(e_integer(4), sx)
            return e_bin_raw(5, [0x68] + src['data'])
        else:
            src = builtin_S(e_integer(1), sx)
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

builtins_std = e_block([
    ('U', e_builtin_func(2, builtin_U)),
    ('S', e_builtin_func(2, builtin_S)),
    ('Bin', e_builtin_func(2, builtin_Bin)),
    ('Ascii', e_builtin_func(2, builtin_Ascii)),
    ('AsciiLength', e_builtin_func(1, builtin_AsciiLength)),
    ('Utf8', e_builtin_func(2, builtin_Utf8)),
    ('Utf8Length', e_builtin_func(1, builtin_Utf8Length)),
    ('Add', e_builtin_func(2, builtin_Add)),
    ('Subtract', e_builtin_func(2, builtin_Subtract)),
    ('mov', e_builtin_func(2, builtin_mov)),
    ('push', e_builtin_func(1, builtin_push)),
    ('pop', e_builtin_func(1, builtin_pop)),
],
                       e_bin_concat([]))

def build():
    return builtins_std
