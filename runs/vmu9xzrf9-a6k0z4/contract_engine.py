import functools
import inspect

def contract(pre=None, post=None):
    """
    Decorator para enforcement de contratos de runtime.
    
    :param pre: Pode ser um dicionário {param_name: lambda} para validação de parâmetros 
                específicos, ou uma lambda(args_dict) para validação global.
    :param post: Uma lambda(args_dict, result) para validar o resultado em relação aos inputs.
    """
    def decorator(func):
        # Otimização: Extrair a assinatura apenas uma vez durante a decoração
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Mapeamento Robusto de Argumentos
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            # args_dict contém todos os argumentos nomeados, incluindo os de *args e **kwargs
            args_dict = bound_args.arguments

            # 2. Validação de Pré-condições
            if pre:
                if isinstance(pre, dict):
                    for param_name, condition in pre.items():
                        # Se o parâmetro for parte de um **kwargs, precisamos buscá-lo lá
                        # Mas o inspect.signature.bind já coloca os itens de **kwargs 
                        # dentro de uma chave com o nome do parâmetro variádico.
                        # Para simplificar e tornar o contrato intuitivo, vamos buscar 
                        # no dicionário principal ou dentro dos sub-dicionários de kwargs.
                        val = args_dict.get(param_name)
                        
                        # Lógica de busca em kwargs se não encontrado na raiz
                        if val is None:
                            for k, v in args_dict.items():
                                if inspect.Parameter.VAR_KEYWORD == sig.parameters[k].kind:
                                    if param_name in v:
                                        val = v[param_name]
                                        break
                        
                        if val is not None:
                            if not condition(val):
                                raise AssertionError(f"[{func.__name__}] Pre-condition failed for '{param_name}'")
                        else:
                            # Se o parâmetro é obrigatório no contrato mas não existe
                            raise AssertionError(f"[{func.__name__}] Pre-condition failed: '{param_name}' not found")
                
                elif callable(pre):
                    # Validação global: passamos o args_dict para a lambda
                    # Para evitar o erro de aninhamento, passamos uma versão "achatada" ou o próprio dict
                    if not pre(args_dict):
                        raise AssertionError(f"[{func.__name__}] Pre-condition failed (global)")

            # 3. Execução da Função
            result = func(*args, **kwargs)

            # 4. Validação de Pós-condições
            if post:
                # Agora a pós-condição recebe (contexto_de_entrada, resultado)
                # Isso permite validar: "o resultado deve ser o dobro do input"
                if not post(args_dict, result):
                    raise AssertionError(f"[{func.__name__}] Post-condition failed")

            return result

        return wrapper
    return decorator

def run_tests():
    print("Iniciando testes de contrato definitivos...\n")

    # Teste 1: Sucesso simples
    @contract(pre={'x': lambda x: x > 0}, post=lambda args, res: res > 0)
    def simple_func(x):
        return x

    assert simple_func(10) == 10
    print("✅ Teste 1 (Sucesso simples) passou.")

    # Teste 2: Falha pré-condição valor
    try:
        simple_func(-1)
    except AssertionError as e:
        assert "Pre-condition failed for 'x'" in str(e)
        print("✅ Teste 2 (Falha pré-condição) passou.")

    # Teste 3: Falha pós-condição
    @contract(post=lambda args, res: res == args['x'] * 2)
    def double_func(x):
        return x + 1 # Erro proposital: deveria ser x * 2

    try:
        double_func(5)
    except AssertionError as e:
        assert "Post-condition failed" in str(e)
        print("✅ Teste 3 (Falha pós-condição) passou.")

    # Teste 4: Keyword arguments e Variádicos (**kwargs)
    @contract(pre={'options': lambda opts: 'key' in opts})
    def process_config(options):
        return True

    @contract(pre={'options': lambda opts: 'key' in opts})
    def process_dynamic(**kwargs):
        return True

    assert process_config(options={'key': 'val'}) is True
    assert process_dynamic(options={'key': 'val'}) is True
    print("✅ Teste 4 (Kwargs e Variádicos) passou.")

    # Teste 5: Falha em Kwargs
    try:
        process_dynamic(options={'wrong': 'val'})
    except AssertionError as e:
        assert "Pre-condition failed for 'options'" in str(e)
        print("✅ Teste 5 (Falha em Kwargs) passou.")

    # Teste 6: Validação Relacional (Pré + Pós)
    @contract(
        pre=lambda args: args['a'] + args['b'] < 10,
        post=lambda args, res: res == args['a'] + args['b']
    )
    def sum_func(a, b):
        return a + b

    assert sum_func(2, 3) == 5
    print("✅ Teste 6 (Validação Relacional) passou.")

    # Teste 7: *args (Posicionais variádicos)
    @contract(pre=lambda args: len(args['nums']) == 3)
    def sum_all(*nums):
        return sum(nums)

    assert sum_all(1, 2, 3) == 6
    print("✅ Teste 7 (*args) passou.")

    # Teste 8: Valores Default
    @contract(pre={'x': lambda x: x == 10})
    def default_func(x=10):
        return x
    
    assert default_func() == 10
    print("✅ Teste 8 (Valores default) passou.")

    # Teste 9: Metadados (Preservação de docstring e nome)
    @contract()
    def metadata_func(x):
        """Docstring original."""
        return x
    assert metadata_func.__name__ == "metadata_func"
    assert metadata_func.__doc__ == "Docstring original."
    print("✅ Teste 9 (Metadados) passou.")

    # Teste 10: Falha Global
    @contract(pre=lambda args: args['x'] > 100)
    def big_number(x):
        return x

    try:
        big_number(50)
    except AssertionError as e:
        assert "Pre-condition failed (global)" in str(e)
        print("✅ Teste 10 (Falha Global) passou.")

    print("\n✨ TODOS OS TESTES PASSARAM COM SUCESSO! ✨")

if __name__ == "__main__":
    run_tests()