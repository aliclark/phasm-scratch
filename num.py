
######## COMMON API ##########

E_INTEGER = 'INT'
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

def builtin_multiply(ix, jx):
    if not ix['final'] or not jx['final']:
        return e_needs_work()
    if ix['type'] != E_INTEGER or jx['type'] != E_INTEGER:
        raise Exception("Multiply takes Integer, Integer arguments")
    return e_integer(ix['data'] * jx['data'])

def builtin_add(ix, jx):
    if not ix['final'] or not jx['final']:
        return e_needs_work()
    if ix['type'] != E_INTEGER or jx['type'] != E_INTEGER:
        raise Exception("Add takes Integer, Integer arguments")
    return e_integer(ix['data'] + jx['data'])

def builtin_subtract(ix, jx):
    if not ix['final'] or not jx['final']:
        return e_needs_work()
    if ix['type'] != E_INTEGER or jx['type'] != E_INTEGER:
        raise Exception("Subtract takes Integer, Integer arguments")
    return e_integer(ix['data'] - jx['data'])

builtins_num = e_block([
    ('add', e_builtin_func(2, builtin_add)),
    ('subtract', e_builtin_func(2, builtin_subtract)),
    ('multiply', e_builtin_func(2, builtin_multiply)),
],
                       e_bin_raw(0, []))

def build():
    return builtins_num
