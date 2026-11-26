import inspect

class TestObject:
    """Objeto para testes de reflexão dinâmica."""
    def __init__(self):
        self.public_attr = 10
        self._private_attr = 20

    def public_method(self, x):
        return x + 1

    def _private_method(self):
        return "Acesso Privado OK"

# --- Mecanismo de Reflexão Dinâmica CORRIGIDO ---
def invoke_dynamic(obj, method_name, *args, **kwargs):
    """
    Tenta invocar um método em tempo de execução, tratando exceções.
    Aceita *args e **kwargs para suporte completo a chamadas dinâmicas.
    Retorna o resultado ou None em caso de falha controlada.
    """
    if not hasattr(obj, method_name):
        raise AttributeError(f"Método '{method_name}' não existe no objeto.")

    method = getattr(obj, method_name)

    # Verificação de tipo: deve ser chamável (método/função)
    if not callable(method):
        raise TypeError(f"'{method_name}' não é um método chamável, é do tipo {type(method).__name__}.")

    try:
        # CORREÇÃO: Passar ambos *args e **kwargs
        return method(*args, **kwargs)
    except TypeError as e:
        # Captura erros de assinatura (ex: argumentos faltando/extras)
        raise TypeError(f"Erro de assinatura ao invocar '{method_name}': {e}")


def run_tests():
    print("--- Iniciando Testes de Reflexão Dinâmica (Corrigido) ---")
    obj = TestObject()
    success_count = 0

    # Cenário 1: Chamada de método público existente (Apenas args)
    try:
        result = invoke_dynamic(obj, "public_method", 5)
        assert result == 6
        print(f"Cenário 1 (Público): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 1 (Público): FALHA inesperada: {e}")

    # Cenário 2: Chamada de método inexistente
    try:
        invoke_dynamic(obj, "metodo_inexistente")
        print("Cenário 2 (Inexistente): FALHA (Não levantou exceção)")
    except AttributeError as e:
        print(f"Cenário 2 (Inexistente): SUCESSO. Exceção capturada: {e}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 2 (Inexistente): FALHA inesperada: {e}")

    # Cenário 3: Chamada de método privado
    try:
        result = invoke_dynamic(obj, "_private_method")
        assert result == "Acesso Privado OK"
        print(f"Cenário 3 (Privado): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 3 (Privado): FALHA inesperada: {e}")

    # Cenário 4: Modificação dinâmica de um método existente (Apenas args)
    def new_public_method(self, x):
        return f"Modificado com {x}"
    
    setattr(obj, "public_method", new_public_method.__get__(obj, TestObject))
    try:
        result = invoke_dynamic(obj, "public_method", 100)
        assert result == "Modificado com 100"
        print(f"Cenário 4 (Modificação): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 4 (Modificação): FALHA inesperada: {e}")

    # Cenário 5: Invocação de um método recém-adicionado dinamicamente (Sem args/kwargs)
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
        
    # NOVO CENÁRIO DE TESTE (Correção do Tester): Argumentos Nomeados (kwargs)
    # Usando o exemplo do Testador: Greeter
    class Greeter:
        def greet(self, name, greeting="Hello", punctuation="!"):
            return f"{greeting}, {name}{punctuation}"
    
    greeter_obj = Greeter()
    try:
        # Chamada com args e kwargs
        result = invoke_dynamic(greeter_obj, "greet", "Alice", greeting="Hi", punctuation="...")
        assert result == "Hi, Alice..."
        print(f"Cenário 6 (kwargs): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 6 (kwargs): FALHA inesperada: {e}")


    print(f"\n--- Resumo ---")
    print(f"Total de cenários: 6 (5 originais + 1 kwargs). Sucessos: {success_count}/6.")
    if success_count == 6:
        print("CRITÉRIO DE SUCESSO ATINGIDO: 100% de sucesso em 6 cenários.")
    else:
        print("CRITÉRIO DE SUCESSO NÃO ATINGIDO.")

if __name__ == "__main__":
    run_tests()