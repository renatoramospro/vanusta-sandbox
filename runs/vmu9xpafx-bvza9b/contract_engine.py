import functools
import inspect

def contract(pre=None, post=None):
    def decorator(func):
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments

            if pre:
                if isinstance(pre, dict):
                    for param_name, condition in pre.items():
                        if param_name in arguments:
                            if not condition(arguments[param_name]):
                                raise AssertionError(
                                    f"[{func.__name__}] Pre-condition failed for parameter '{param_name}'"
                                )
                        else:
                            raise AssertionError(
                                f"[{func.__name__}] Pre-condition failed: parameter '{param_name}' not found"
                            )
                elif callable(pre):
                    if not pre(arguments):
                        raise AssertionError(f"[{func.__name__}] Pre-condition failed (global)")

            result = func(*args, **kwargs)

            if post:
                if not post(result):
                    raise AssertionError(
                        f"[{func.__name__}] Post-condition failed: result {result} violated contract"
                    )

            return result

        return wrapper
    return decorator

def run_tests():
    print("Iniciando testes de contrato...\n")
    
    @contract(pre={'x': lambda x: x > 0}, post=lambda res: res > 0)
    def positive_increment(x):
        return x + 1

    assert positive_increment(5) == 6
    print("✅ Teste 1 (Sucesso simples) passou.")

    try:
        positive_increment(-1)
    except AssertionError as e:
        assert "[positive_increment] Pre-condition failed for parameter 'x'" in str(e)
        print("✅ Teste 2 (Falha pré-condição valor) passou.")
    else:
        raise Exception("❌ Teste 2 falhou")

    @contract(post=lambda res: res < 10)
    def small_number(x):
        return x

    try:
        small_number(15)
    except AssertionError as e:
        assert "[small_number] Post-condition failed" in str(e)
        print("✅ Teste 3 (Falha pós-condição) passou.")
    else:
        raise Exception("❌ Teste 3 falhou")

    @contract(pre={'a': lambda a: a > 0})
    def add(a, b):
        return a + b

    assert add(a=10, b=5) == 15
    print("✅ Teste 4 (Keyword arguments) passou.")

    @contract(pre=lambda args: len(args['nums']) > 0)
    def sum_all(*nums):
        return sum(nums)

    assert sum_all(1, 2, 3) == 6
    print("✅ Teste 5 (*args) passou.")

    @contract(pre=lambda args: 'key' in args.get('options', {}))
    def process_config(**options):
        return True

    assert process_config(options={'key': 'val'}) is True
    print("✅ Teste 6 (**kwargs) passou.")

    try:
        sum_all()
    except AssertionError as e:
        assert "[sum_all] Pre-condition failed (global)" in str(e)
        print("✅ Teste 7 (Falha *args) passou.")
    else:
        raise Exception("❌ Teste 7 falhou")

    @contract(pre=lambda args: args['a'] + args['b'] == 10)
    def strict_sum(a, b):
        return a + b

    assert strict_sum(3, 7) == 10
    try:
        strict_sum(1, 1)
    except AssertionError as e:
        assert "[strict_sum] Pre-condition failed (global)" in str(e)
        print("✅ Teste 8 (Contrato global) passou.")
    else:
        raise Exception("❌ Teste 8 falhou")

    @contract(pre={'x': lambda x: True})
    def metadata_func(x):
        """Docstring original."""
        return x
    
    assert metadata_func.__name__ == "metadata_func"
    assert metadata_func.__doc__ == "Docstring original."
    print("✅ Teste 9 (Metadados) passou.")

    @contract(pre={'x': lambda x: x == 10})
    def default_func(x=10):
        return x
    
    assert default_func() == 10
    print("✅ Teste 10 (Valores default) passou.")

    print("\n✨ TODOS OS TESTES PASSARAM COM SUCESSO! ✨")

if __name__ == "__main__":
    run_tests()