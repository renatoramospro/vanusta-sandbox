class Validator:
    """
    Um Data Descriptor que valida o tipo e o intervalo de valores.
    """
    def __init__(self, name, expected_type, min_val=None, max_val=None):
        self.name = name
        self.expected_type = expected_type
        self.min_val = min_val
        self.max_val = max_val
        # O nome interno onde o valor será guardado na instância
        self.internal_name = f"_{name}"

    def __get__(self, instance, owner):
        # Se acessado via Classe (ex: Pessoa.idade), retorna o próprio descritor
        if instance is None:
            return self
        
        # Busca o valor no __dict__ da instância para evitar estado compartilhado
        return getattr(instance, self.internal_name, None)

    def __set__(self, instance, value):
        # 1. Validação de Tipo
        if not isinstance(value, self.expected_type):
            raise TypeError(f"Atributo '{self.name}' deve ser {self.expected_type.__name__}, mas recebeu {type(value).__name__}")

        # 2. Validação de Range (apenas para tipos numéricos)
        if isinstance(value, (int, float)):
            if self.min_val is not None and value < self.min_val:
                raise ValueError(f"Atributo '{self.name}' deve ser >= {self.min_val}")
            if self.max_val is not None and value > self.max_val:
                raise ValueError(f"Atributo '{self.name}' deve ser <= {self.max_val}")

        # 3. Armazenamento seguro no __dict__ da instância
        setattr(instance, self.internal_name, value)

    def __delete__(self, instance):
        if hasattr(instance, self.internal_name):
            delattr(instance, self.internal_name)
        else:
            raise AttributeError(f"Atributo '{self.name}' não definido.")

class Sensor:
    # Definição dos descritores na classe
    temperatura = Validator("temperatura", float, min_val=-50.0, max_val=100.0)
    id_sensor = Validator("id_sensor", int)

    def __init__(self, id_sensor, temperatura):
        self.id_sensor = id_sensor
        self.temperatura = temperatura

def run_experiment():
    print("--- Iniciando Experimento de Descritores ---\n")

    # Teste 1: Atribuição correta
    s1 = Sensor(1, 25.5)
    print(f"[OK] Sensor 1 criado: ID={s1.id_sensor}, Temp={s1.temperatura}")
    assert s1.id_sensor == 1
    assert s1.temperatura == 25.5

    # Teste 2: Validação de Tipo (Erro esperado)
    print("[Teste] Tentando atribuir string à temperatura...")
    try:
        s1.temperatura = "quente"
    except TypeError as e:
        print(f"[Capturado] Erro de tipo esperado: {e}")
    else:
        raise AssertionError("Falha: Deveria ter lançado TypeError")

    # Teste 3: Validação de Range (Erro esperado)
    print("[Teste] Tentando atribuir temperatura fora do range (150.0)...")
    try:
        s1.temperatura = 150.0
    except ValueError as e:
        print(f"[Capturado] Erro de valor esperado: {e}")
    else:
        raise AssertionError("Falha: Deveria ter lançado ValueError")

    # Teste 4: Independência de Instâncias (O ponto crucial)
    print("[Teste] Verificando independência de instâncias...")
    s2 = Sensor(2, 30.0)
    s1.temperatura = 10.0
    print(f"  S1 Temp: {s1.temperatura}")
    print(f"  S2 Temp: {s2.temperatura}")
    if s1.temperatura != s2.temperatura:
        print("[OK] Instâncias são independentes.")
    else:
        raise AssertionError("Falha: As instâncias compartilham o mesmo valor!")

    # Teste 5: Deleção
    print("[Teste] Testando deleção de atributo...")
    del s1.temperatura
    try:
        print(f"  S1 Temp após deleção: {s1.temperatura}")
    except Exception:
        print("  [OK] Atributo removido com sucesso.")

    print("\n--- Experimento Concluído com SUCESSO ---")

if __name__ == "__main__":
    run_experiment()