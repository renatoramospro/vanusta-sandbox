import functools
import inspect

def contract(pre=None, post=None):
    """
    Decorator para enforcement de contratos de runtime.
    
    :param pre: Pode ser um dicionário {param_name: lambda} para validação de parâmetros 
                específicos, ou uma lambda(args_dict) para validação global.
    :param post: Uma lambda(result) para validar o valor de retorno.
    """
    def decorator(func):
        # Otimização: Extrair a assinatura apenas uma vez durante a decoração
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Mapeamento Robusto de Argumentos
            # O bind() resolve a complexidade de *args, **kwargs e valores default
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            args_dict = bound_args.arguments

            # 2. Validação de Pré-condições
            if pre:
                if isinstance(pre, dict):
                    # Validação por parâmetro específico
                    for param_name, condition in pre.items():
                        if param_name in args_dict:
                            if not condition(args_dict[param_name]):
                                raise AssertionError(
                                    f"[{func.__name__}] Pre-condition failed for parameter '{param_name}'"
                                )
                        else:
                            # Se o parâmetro exigido no contrato não está nos argumentos
                            raise AssertionError(
                                f"[{func.__name__}] Pre-condition failed: parameter '{param_name}' not found"
                            )
                elif callable(pre):
                    # Validação global (recebe o dicionário completo de argumentos)
                    if not pre(args_dict):
                        raise AssertionError(f"[{func.__name__}] Pre-condition failed (global)")

            # 3. Execução da Função Original
            result = func(*args, **kwargs)

            # 4. Validação de Pós-condições
            if post:
                if not post(result):
                    raise AssertionError(f"[{func.__name__}] Post-condition failed")

            return result

        return wrapper
    return decorator

def run_tests():
    print("Iniciando testes de contrato corrigidos...\n")

    # Teste 1: Sucesso simples
    @contract(pre={'x': lambda x: x > 0})
    def simple_func(x):
        return x
    assert simple_func(10) == 10
    print("✅ Teste 1 (Sucesso simples) passou.")

    # Teste 2: Falha pré-condição valor
    try:
        simple_func(-1)
    except AssertionError as e:
        assert "[simple_func] Pre-condition failed for parameter 'x'" in str(e)
        print("✅ Teste 2 (Falha pré-condição valor) passou.")
    else:
        raise Exception("❌ Teste 2 falhou")

    # Teste 3: Falha pós-condição
    @contract(post=lambda res: res > 10)
    def post_fail(x):
        return x
    try:
        post_fail(5)
    except AssertionError as e:
        assert "[post_fail] Post-condition failed" in str(e)
        print("✅ Teste 3 (Falha pós-condição) passou.")
    else:
        raise Exception("❌ Teste 3 falhou")

    # Teste 4: Keyword arguments
    @contract(pre={'a': lambda a: a == 1})
    def kw_func(a, b):
        return a + b
    assert kw_func(a=1, b=2) == 3
    print("✅ Teste 4 (Keyword arguments) passou.")

    # Teste 5: *args
    @contract(pre=lambda args: len(args['nums']) > 0)
    def sum_all(*nums):
        return sum(nums)
    assert sum_all(1, 2, 3) == 6
    print("✅ Teste 5 (*args) passou.")

    # Teste 6: **kwargs (Onde o erro anterior ocorria)
    # O bind() coloca o conteúdo de **kwargs dentro de uma chave no args_dict
    @contract(pre=lambda args: args.get('options', {}).get('key') == 'val')
    def process_config(**options):
        return True
    assert process_config(options={'key': 'val'}) is True
    print("✅ Teste 6 (**kwargs) passou.")

    # Teste 7: Falha *args (Global)
    try:
        sum_all()
    except AssertionError as e:
        assert "[sum_all] Pre-condition failed (global)" in str(e)
        print("✅ Teste 7 (Falha *args) passou.")
    else:
        raise Exception("❌ Teste 7 falhou")

    # Teste 8: Contrato global com argumentos nomeados
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

    # Teste 9: Metadados
    @contract(pre={'x': lambda x: True})
    def metadata_func(x):
        """Docstring original."""
        return x
    assert metadata_func.__name__ == "metadata_func"
    assert metadata_func.__doc__ == "Docstring original."
    print("✅ Teste 9 (Metadados) passou.")

    # Teste 10: Valores default
    @contract(pre={'x': lambda x: x == 10})
    def default_func(x=10):
        return x
    assert default_func() == 10
    print("✅ Teste 10 (Valores default) passou.")

    print("\n✨ TODOS OS TESTES PASSARAM COM SUCESSO! ✨")

if __name__ == "__main__":
    run_tests()