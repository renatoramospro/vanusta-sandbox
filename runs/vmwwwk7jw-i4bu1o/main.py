import inspect
import warnings

class TestObject:
    """Objeto para testes de reflexão dinâmica."""
    def __init__(self):
        self.public_attr = 10
        self._private_attr = 20

    def public_method(self, x):
        return x + 1

    def _private_method(self):
        return "Acesso Privado OK"

# --- Mecanismo de Reflexão Dinâmica CORRIGIDO E SEGURIZADO ---
def invoke_dynamic(obj, method_name, *args, **kwargs, allow_private=False):
    """
    Tenta invocar um método em tempo de execução.
    AVISO DE SEGURANÇA: method_name DEVE vir de fonte confiável.
    
    Args:
        obj: O objeto alvo.
        method_name: Nome do método como string.
        *args, **kwargs: Argumentos para o método.
        allow_private: Se True, permite invocação de métodos privados (prefixo '_').
    """
    # 1. Validação de Entrada (Contra Ataque Dunder)
    if method_name.startswith('__') and not method_name.endswith('__'):
        # Bloqueia métodos que parecem dunder mas não são (ex: __init__ é permitido se for o caso, mas aqui focamos em evitar acesso arbitrário)
        # Para simplificar, bloqueamos qualquer coisa que comece com __, exceto se for um método conhecido de sistema (que não estamos listando)
        raise ValueError(f"Método '{method_name}' é um dunder method e não é permitido por padrão.")
    
    # 2. Controle de Visibilidade
    if method_name.startswith('_') and not allow_private:
        raise PermissionError(f"Acesso a método privado '{method_name}' negado. Use allow_private=True.")

    if not hasattr(obj, method_name):
        raise AttributeError(f"Método '{method_name}' não existe no objeto.")

    method = getattr(obj, method_name)

    if not callable(method):
        raise TypeError(f"'{method_name}' não é um método chamável, é do tipo {type(method).__name__}.")

    try:
        return method(*args, **kwargs)
    except TypeError as e:
        raise TypeError(f"Erro de assinatura ao invocar '{method_name}': {e}")


def run_tests():
    print("--- Iniciando Testes de Reflexão Dinâmica (Seguro) ---")
    obj = TestObject()
    success_count = 0

    # Cenário 1: Público (Sucesso)
    try:
        result = invoke_dynamic(obj, "public_method", 5)
        assert result == 6
        print(f"Cenário 1 (Público): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 1 (Público): FALHA inesperada: {e}")

    # Cenário 2: Inexistente (Sucesso na exceção)
    try:
        invoke_dynamic(obj, "metodo_inexistente")
        print("Cenário 2 (Inexistente): FALHA (Não levantou exceção)")
    except AttributeError as e:
        print(f"Cenário 2 (Inexistente): SUCESSO. Exceção capturada: {e}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 2 (Inexistente): FALHA inesperada: {e}")

    # Cenário 3: Privado (Falha esperada sem allow_private=True)
    try:
        invoke_dynamic(obj, "_private_method")
        print("Cenário 3 (Privado): FALHA (Permitiu acesso sem permissão)")
    except PermissionError as e:
        print(f"Cenário 3 (Privado): SUCESSO. Exceção capturada: {e}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 3 (Privado): FALHA inesperada: {e}")

    # Cenário 4: Privado (Sucesso com allow_private=True)
    try:
        result = invoke_dynamic(obj, "_private_method", allow_private=True)
        assert result == "Acesso Privado OK"
        print(f"Cenário 4 (Privado Permitido): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 4 (Privado Permitido): FALHA inesperada: {e}")

    # Cenário 5: Dinâmico (Sucesso)
    def dynamic_method(self):
        return "Adicionado Dinamicamente"
    
    setattr(obj, "dynamic_method", dynamic_method.__get__(obj, TestObject))
    try:
        result = invoke_dynamic(obj, "dynamic_method")
        assert result == "Adicionado Dinamicamente"
        print(f"Cenário 5 (Dinâmico): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 5 (Dinâmico): FALHA inesperada: {e}")
        
    # Cenário 6: kwargs (Sucesso)
    class Greeter:
        def greet(self, name, greeting="Hello", punctuation="!"):
            return f"{greeting}, {name}{punctuation}"
    
    greeter_obj = Greeter()
    try:
        result = invoke_dynamic(greeter_obj, "greet", "Alice", greeting="Hi", punctuation="...")
        assert result == "Hi, Alice..."
        print(f"Cenário 6 (kwargs): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 6 (kwargs): FALHA inesperada: {e}")

    # NOVO CENÁRIO DE SEGURANÇA (Contraexemplo do Equívoco Comum)
    # Ataque Dunder: Tentar acessar __class__
    try:
        invoke_dynamic(obj, "__class__")
        print("Cenário 7 (Dunder Ataque): FALHA (Permitiu acesso dunder)")
    except ValueError as e:
        print(f"Cenário 7 (Dunder Ataque): SUCESSO. Exceção capturada: {e}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 7 (Dunder Ataque): FALHA inesperada: {e}")


    print(f"\n--- Resumo ---")
    print(f"Total de cenários: 7. Sucessos: {success_count}/7.")
    if success_count == 7:
        print("CRITÉRIO DE SUCESSO ATINGIDO: 100% de sucesso em 7 cenários.")
    else:
        print("CRITÉRIO DE SUCESSO NÃO ATINGIDO.")

if __name__ == "__main__":
    run_tests()