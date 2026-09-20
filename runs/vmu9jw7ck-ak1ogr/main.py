class Validator:
    """
    Um Data Descriptor robusto que valida tipos e limites, 
    protegido contra manipulação direta do __dict__ da instância.
    """
    def __init__(self, name, expected_type, min_val=None, max_val=None):
        self.name = name
        self.expected_type = expected_type
        self.min_val = min_val
        self.max_val = max_val
        # Mitigação de Colisão: Nome interno altamente específico
        self._internal_key = f"__v_data_{id(self)}_{name}__"

    def _validate(self, value):
        """Centraliza a lógica de validação para uso em __set__ e __get__."""
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"Atributo '{self.name}' deve ser {self.expected_type.__name__}, "
                f"mas recebeu {type(value).__name__}"
            )
        
        if isinstance(value, (int, float)):
            if self.min_val is not None and value < self.min_val:
                raise ValueError(f"Atributo '{self.name}' deve ser >= {self.min_val}")
            if self.max_val is not None and value > self.max_val:
                raise ValueError(f"Atributo '{self.name}' deve ser <= {self.max_val}")

    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        # Recupera o valor do dicionário da instância
        value = getattr(instance, self._internal_key, None)
        
        # Mitigação de Bypass: Se o valor existe, revalida antes de entregar.
        # Isso impede que manipulações via __dict__ passem despercebidas.
        if value is not None:
            try:
                self._validate(value)
            except (TypeError, ValueError) as e:
                raise RuntimeError(f"Integridade de dados violada no atributo '{self.name}': {e}") from e
        
        return value

    def __set__(self, instance, value):
        # Valida antes de persistir
        self._validate(value)
        setattr(instance, self._internal_key, value)

    def __delete__(self, instance):
        if hasattr(instance, self._internal_key):
            delattr(instance, self._internal_key)

class Sensor:
    temperatura = Validator("temperatura", float, min_val=-50.0, max_val=150.0)
    pressao = Validator("pressao", float, min_val=0.0, max_val=10.0)

def run_security_experiment():
    print("--- Iniciando Experimento de Segurança (Mitigação de Bypass) ---")
    s1 = Sensor()
    s1.temperatura = 25.5
    
    print(f"[1] Valor legítimo: {s1.temperatura}")

    # Teste 1: Tentativa de bypass via __dict__
    print("\n[2] Tentando bypass via manipulação direta do __dict__...")
    # O atacante tenta injetar uma string onde deveria haver um float
    s1.__dict__[s1.temperatura._internal_key] = "CORRUPTO" 
    # Nota: Usamos o internal_key para simular o acesso ao local exato onde o dado reside
    
    # No código acima, o atacante não sabe o nome da chave, mas vamos simular o acesso:
    key_to_attack = s1.temperatura._internal_key
    s1.__dict__[key_to_attack] = "CORRUPTO"

    try:
        print(f"Tentando ler s1.temperatura após ataque...")
        print(s1.temperatura)
    except RuntimeError as e:
        print(f"[SUCESSO] Bypass detectado e bloqueado: {e}")
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {type(e).__name__}: {e}")

    # Teste 2: Verificação de colisão de nomes
    print("\n[3] Verificando isolamento de nomes internos...")
    s2 = Sensor()
    s2.temperatura = 10.0
    s2.pressao = 5.0
    
    # Se os nomes internos fossem apenas '_temperatura', um erro de digitação ou 
    # colisão de atributos de instância poderia causar problemas.
    # Verificamos se as chaves são distintas.
    if s1.temperatura._internal_key != s1.pressao._internal_key:
        print("[SUCESSO] Chaves internas são únicas e protegidas contra colisão.")
    else:
        print("[FALHA] Colisão de chaves detectada!")

    # Teste 3: Independência de instâncias
    print("\n[4] Verificando independência de instâncias...")
    s1.temperatura = 20.0
    s2.temperatura = 30.0
    if s1.temperatura == 20.0 and s2.temperatura == 30.0:
        print("[SUCESSO] Instâncias mantêm estados independentes.")
    else:
        print("[FALHA] Estado compartilhado detectado!")

    print("\n--- Experimento de Segurança Concluído ---")

if __name__ == "__main__":
    run_security_experiment()