
import string

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

def builtin_ascii(ix, sx):
    return generic_python_encode(ix, sx, 'ascii')

def builtin_ascii_length(sx):
    return generic_python_length(sx, 'ascii')

def builtin_utf8(ix, sx):
    return generic_python_encode(ix, sx, 'utf8')

def builtin_utf8_length(sx):
    return generic_python_length(sx, 'utf8')

builtins_str = e_block([
    ('ascii', e_builtin_func(2, builtin_ascii)),
    ('ascii_length', e_builtin_func(1, builtin_ascii_length)),
    ('utf8', e_builtin_func(2, builtin_utf8)),
    ('utf8_length', e_builtin_func(1, builtin_utf8_length)),
],
                       e_bin_raw(0, []))

def build():
    return builtins_str
