import sys

class CoreEngine:
    """Representa o motor do jogo. O estado é privado e inacessível externamente."""
    def __init__(self):
        self._entities = {
            "player_1": {"health": 100, "mana": 50}
        }

    def get_entity_data(self, entity_id):
        return self._entities.get(entity_id)

    def update_entity_attribute(self, entity_id, attr, value):
        # A Bridge chamará este método após validação
        if entity_id in self._entities and attr in self._entities[entity_id]:
            self._entities[entity_id][attr] = value
            return True
        return False

class ModdingBridge:
    """A camada de tradução e validação (Security Layer)."""
    def __init__(self, engine):
        self.engine = engine

    def safe_set_health(self, entity_id, value):
        # Regra de negócio: impede que mods coloquem vida negativa ou impossível
        if 0 <= value <= 100:
            return self.engine.update_entity_attribute(entity_id, "health", value)
        print(f"[Bridge] REJEITADO: Valor de vida {value} fora dos limites permitidos.")
        return False

class PlayerProxy:
    """O objeto entregue ao Modder. Não contém dados, apenas comandos."""
    def __init__(self, entity_id, bridge):
        self._entity_id = entity_id
        self._bridge = bridge

    def set_health(self, value):
        return self._bridge.safe_set_health(self._entity_id, value)

    def __getattr__(self, name):
        # Impede o acesso a qualquer atributo que não foi explicitamente definido
        raise AttributeError(f"Acesso negado ao atributo '{name}'. Use os métodos da API.")

class Sandbox:
    """Gerencia a execução de scripts externos."""
    def __init__(self, bridge):
        self.bridge = bridge

    def execute_mod(self, mod_code, proxy_object):
        # Criamos um ambiente restrito (Namespace)
        # Removemos __builtins__ para impedir 'import os', 'open', etc.
        safe_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "int": int
            },
            "player": proxy_object
        }
        
        try:
            print(f"\n--- Iniciando Execução do Mod ---")
            exec(mod_code, safe_globals)
            print("--- Execução Finalizada com Sucesso ---")
        except Exception as e:
            print(f"[Sandbox] INTERCEPTADO: O mod tentou uma operação proibida ou falhou: {e}")

# --- TESTES DO EXPERIMENTO ---

def run_experiment():
    engine = CoreEngine()
    bridge = ModdingBridge(engine)
    sandbox = Sandbox(bridge)
    
    # O Proxy que o modder receberá
    player_proxy = PlayerProxy("player_1", bridge)

    # CASO 1: Mod Legítimo
    # O modder usa a API permitida para alterar a vida.
    mod_legitimo = """
print("Mod: Tentando alterar vida para 50...")
player.set_health(50)
"""

    # CASO 2: Tentativa de Hack de Atributo (Ataque de Memória/Encapsulamento)
    # O modder tenta ignorar a API e escrever diretamente no atributo 'health'.
    # Como o Proxy não tem o atributo 'health', isso deve falhar.
    mod_hack_atributo = """
print("Mod: Tentando hack direto via player.health = 999...")
player.health = 999
"""

    # CASO 3: Tentativa de Escape de Sandbox (Ataque de Sistema)
    # O modder tenta importar o módulo 'os' para manipular arquivos do sistema.
    mod_hack_sistema = """
print("Mod: Tentando importar módulo 'os' para deletar arquivos...")
import os
os.system('echo hack')
"""

    # Execução
    sandbox.execute_mod(mod_legitimo, player_proxy)
    print(f"Estado do Core (Vida): {engine.get_entity_data('player_1')['health']}")

    sandbox.execute_mod(mod_hack_atributo, player_proxy)
    print(f"Estado do Core (Vida) após tentativa de hack: {engine.get_entity_data('player_1')['health']}")

    sandbox.execute_mod(mod_hack_sistema, player_proxy)
    print(f"Estado do Core (Vida) após tentativa de escape: {engine.get_entity_data('player_1')['health']}")

    # Verificação Final: O motor deve continuar intacto e rodando
    print("\n[Final] Engine está operando normalmente.")

if __name__ == "__main__":
    run_experiment()