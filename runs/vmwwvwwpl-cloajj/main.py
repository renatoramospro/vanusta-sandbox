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

# --- Mecanismo de Reflexão Dinâmica ---
def invoke_dynamic(obj, method_name, *args):
    """
    Tenta invocar um método em tempo de execução, tratando exceções.
    Retorna o resultado ou None em caso de falha controlada.
    """
    if not hasattr(obj, method_name):
        raise AttributeError(f"Método '{method_name}' não existe no objeto.")

    method = getattr(obj, method_name)

    # Verificação de tipo: deve ser chamável (método/função)
    if not callable(method):
        raise TypeError(f"'{method_name}' não é um método chamável, é do tipo {type(method).__name__}.")

    # Cenário de segurança/acesso: Embora Python não force encapsulamento estrito,
    # tentamos respeitar a intenção (métodos privados começam com '_').
    if method_name.startswith('_') and not inspect.isroutine(method):
        # Se for um atributo privado que não é uma função, tratamos como erro de acesso
        pass # Permitimos a chamada se for um método, mas registramos a intenção.

    try:
        return method(*args)
    except Exception as e:
        # Captura exceções internas do método (ex: TypeError se argumentos errados)
        raise RuntimeError(f"Erro ao executar '{method_name}': {e}")

# --- Cenários de Teste ---
def run_tests():
    obj = TestObject()
    print("--- Iniciando Testes de Reflexão Dinâmica ---")
    success_count = 0
    
    # Cenário 1: Chamada de método público existente
    try:
        result = invoke_dynamic(obj, "public_method", 5)
        assert result == 6
        print(f"Cenário 1 (Público): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 1 (Público): FALHA inesperada: {e}")

    # Cenário 2: Chamada de método inexistente (Deve levantar AttributeError)
    try:
        invoke_dynamic(obj, "metodo_inexistente")
        print("Cenário 2 (Inexistente): FALHA. Não levantou AttributeError.")
    except AttributeError as e:
        print(f"Cenário 2 (Inexistente): SUCESSO. Exceção capturada: {e}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 2 (Inexistente): FALHA. Levantou exceção errada: {type(e).__name__}")

    # Cenário 3: Chamada de método privado (Deve funcionar em Python, mas é testado)
    try:
        result = invoke_dynamic(obj, "_private_method")
        assert result == "Acesso Privado OK"
        print(f"Cenário 3 (Privado): SUCESSO. Resultado: {result}")
        success_count += 1
    except Exception as e:
        print(f"Cenário 3 (Privado): FALHA inesperada: {e}")

    # Cenário 4: Modificação dinâmica de um método existente
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

    # Cenário 5: Invocação de um método recém-adicionado dinamicamente
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

    print(f"\n--- Resumo ---")
    print(f"Total de cenários: 5. Sucessos: {success_count}/5.")
    if success_count == 5:
        print("CRITÉRIO DE SUCESSO ATINGIDO: 100% de sucesso em 5 cenários.")
    else:
        print("CRITÉRIO DE SUCESSO NÃO ATINGIDO.")

if __name__ == "__main__":
    run_tests()