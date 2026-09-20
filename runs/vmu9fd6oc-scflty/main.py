print('teste-falha: antes do erro')
def f():
    raise ValueError('falha proposital do teste')
f()
