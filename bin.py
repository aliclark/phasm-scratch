
import string

######## COMMON API ##########

E_INTEGER = 'INT'
E_STRING  = 'STR'
E_BIN_RAW = 'RAW'
E_BLOCK   = 'BLK'
E_OFFSET_LABEL = 'OFF'
E_BIN_CONCAT   = 'BINCAT'
E_BUILTIN_FUNC = 'BUILTIN'
E_NEEDS_WORK   = 'NEEDS_WORK'

def e_needs_work(length=None):
    return {'len': length, 'final': False, 'type':E_NEEDS_WORK, 'data': None}

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

def get_bin_concat_len(lst):
    lens = [x['len'] for x in lst]
    if not any([l is None for l in lens]):
        return sum(lens)
    return None

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

def builtin_bin(ix, sx):
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

def builtin_unsigned(ix, jx):
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

# TODO: other functions will do truncation and big endian in future

builtins_bin = e_block([
    ('unsigned', e_builtin_func(2, builtin_unsigned)),
    ('signed',   e_builtin_func(2, builtin_signed)),
    ('bin',      e_builtin_func(2, builtin_bin)),
],
                       e_bin_raw(0, []))

def build():
    return builtins_bin
