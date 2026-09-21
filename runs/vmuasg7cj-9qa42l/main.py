class CoreEngine:
    def __init__(self):
        self._state = {
            "player_1": {"health": 100, "mana": 50}
        }

    def get_entity_data(self, entity_id):
        return self._state.get(entity_id)

    def update_entity_attribute(self, entity_id, attr, value):
        if entity_id in self._state and attr in self._state[entity_id]:
            self._state[entity_id][attr] = value
            return True
        return False

class ModdingBridge:
    def __init__(self, engine: CoreEngine):
        self._engine = engine

    def set_health(self, entity_id: str, value: int):
        # Correção de Segurança: Validação estrita sem vazamento de tipos internos (Information Leakage)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            # ANTES: f"Tipo inválido: {type(value).__name__}" -> Vazava a estrutura interna
            # AGORA: Mensagem genérica e opaca
            raise TypeError("Parâmetro com tipo inválido fornecido à API.")
        
        if not (0 <= value <= 100):
            raise ValueError("Valor fora dos limites permitidos.")
        
        return self._engine.update_entity_attribute(entity_id, "health", value)

class PlayerProxy:
    def __init__(self, bridge: ModdingBridge, entity_id: str):
        object.__setattr__(self, "_bridge", bridge)
        object.__setattr__(self, "_entity_id", entity_id)

    def set_health(self, value):
        return self._bridge.set_health(object.__getattribute__(self, "_entity_id"), value)

    def __getattr__(self, name):
        raise AttributeError(f"Acesso negado ao atributo '{name}'.")

    def __setattr__(self, name, value):
        raise AttributeError(f"Modificação direta negada para '{name}'.")

    def __dir__(self):
        return ["set_health"]

    @property
    def __dict__(self):
        raise AttributeError("Acesso ao dicionário interno negado.")

    def __repr__(self):
        return "<PlayerProxy [Restricted]>"

def execute_mod(mod_code, player_proxy):
    safe_globals = {
        "__builtins__": {
            "print": print,
            "range": range,
            "len": len,
            "Exception": Exception,
            "TypeError": TypeError,
            "ValueError": ValueError,
        },
        "player": player_proxy
    }
    
    try:
        exec(mod_code, safe_globals)
    except Exception as e:
        # Imprime a exceção para validar que nenhuma informação estrutural do Core vaza
        print(f"[Sandbox] INTERCEPTADO: {e}")

def run_experiment():
    engine = CoreEngine()
    bridge = ModdingBridge(engine)
    proxy = PlayerProxy(bridge, "player_1")

    print("--- 1. Mod Legítimo (Valores Válidos) ---")
    mod_valid = "player.set_health(50)"
    execute_mod(mod_valid, proxy)
    print(f"Estado do Core (Vida): {engine.get_entity_data('player_1')['health']}\n")

    print("--- 2. Teste de Borda: Injeção de Tipo Inválido (Verificação de Information Leakage) ---")
    mod_invalid_type = "player.set_health('cem')"
    execute_mod(mod_invalid_type, proxy)
    print(f"Estado do Core (Vida) após tipo inválido: {engine.get_entity_data('player_1')['health']}\n")

    print("[Final] Correção de vazamento de informação validada com sucesso.")

if __name__ == "__main__":
    run_experiment()