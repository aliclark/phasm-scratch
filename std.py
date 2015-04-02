
import string

from common import *

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
        raise Exception("S takes Integer, Integer arguments")
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
],
                       e_bin_concat([]))

def build():
    return builtins_std
