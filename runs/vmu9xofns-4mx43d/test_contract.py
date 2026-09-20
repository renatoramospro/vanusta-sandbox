import inspect
from functools import wraps

def contract(pre=None, post=None):
    """
    Decorador para impor contratos de pré-condição e pós-condição em funções Python.
    
    :param pre: Lambda ou callable que recebe os argumentos nomeados da função e retorna bool.
    :param post: Lambda ou callable que recebe (result, **arguments) ou (result) e retorna bool.
    """
    def decorator(func):
        sig = inspect.signature(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Mapeia args e kwargs para os nomes dos parâmetros da função
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments

            # Validação da Pré-condição
            if pre is not None:
                # Se a lambda espera argumentos, passamos via **arguments
                try:
                    passed = pre(**arguments)
                except TypeError:
                    # Caso a pré-condição não aceite argumentos (ex: lambda: x > 0 sem escopo)
                    passed = pre()
                
                if not passed:
                    cond_str = inspect.getsource(pre).strip()
                    raise AssertionError(
                        f"Contrato violado [Pré-condição] na função '{func.__name__}': {cond_str}"
                    )

            # Execução da função original
            result = func(*args, **kwargs)

            # Validação da Pós-condição
            if post is not None:
                try:
                    # Tenta passar o resultado e os argumentos
                    passed = post(result, **arguments)
                except TypeError:
                    try:
                        passed = post(result)
                    except TypeError:
                        passed = post()

                if not passed:
                    cond_str = inspect.getsource(post).strip()
                    raise AssertionError(
                        f"Contrato violado [Pós-condição] na função '{func.__name__}': {cond_str}"
                    )

            return result
        return wrapper
    return decorator


# --- Testes Automatizados ---

def test_successful_contract():
    @contract(pre=lambda x, y: x > 0 and y > 0, post=lambda result, x, y: result == x + y)
    def somar_positivos(x, y):
        return x + y

    assert somar_positivos(2, 3) == 5
    print("-> test_successful_contract passou com sucesso.")


def test_precondition_failure():
    @contract(pre=lambda idade: idade >= 18)
    def maior_de_idade(idade):
        return f"Acesso permitido para {idade}"

    try:
        maior_de_idade(15)
        raise AssertionError("Deveria ter falhado na pré-condição.")
    except AssertionError as e:
        msg = str(e)
        assert "maior_de_idade" in msg
        assert "Pré-condição" in msg
        print(f"-> test_precondition_failure capturou corretamente: {e}")


def test_postcondition_failure():
    @contract(post=lambda result: result % 2 == 0)
    def retornar_numero(n):
        return n

    try:
        retornar_numero(3)
        raise AssertionError("Deveria ter falhado na pós-condição.")
    except AssertionError as e:
        msg = str(e)
        assert "retornar_numero" in msg
        assert "Pós-condição" in msg
        print(f"-> test_postcondition_failure capturou corretamente: {e}")


def test_variadic_arguments():
    @contract(pre=lambda args: len(args) > 0)
    def processar(*args):
        return sum(args)

    # Testando com mapeamento correto de args
    @contract(pre=lambda x, **kwargs: x > 0)
    def complexa(x, *args, **kwargs):
        return x

    assert complexa(10, 1, 2, a=3) == 10
    print("-> test_variadic_arguments passou com sucesso.")


if __name__ == "__main__":
    print("Iniciando testes do Runtime Contract Enforcement...")
    test_successful_contract()
    test_precondition_failure()
    test_postcondition_failure()
    test_variadic_arguments()
    print("Todos os testes executados com sucesso absoluto!")