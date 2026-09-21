import json
import time
import hashlib

# --- CAMADA DE DOMÍNIO (Estado do Jogo) ---
class PlayerState:
    """Representa o estado atual do jogador no jogo (v2)."""
    def __init__(self, name: str, health: int, stamina: int):
        self.name = name
        self.health = health
        self.stamina = stamina

    def __eq__(self, other):
        if not isinstance(other, PlayerState):
            return False
        return (self.name == other.name and 
                self.health == other.health and 
                self.stamina == other.stamina)

# --- CAMADA DE EVOLUÇÃO (Migração) ---
class MigrationManager:
    """Gerencia a transição de schemas entre versões."""
    
    @staticmethod
    def migrate(data: dict) -> dict:
        version = data.get("version", 1)
        
        # Migração v1 -> v2: Adiciona 'stamina' que não existia na v1
        if version == 1:
            print(f"[Migration] Migrando schema v1 para v2...")
            data["stamina"] = 100  # Valor padrão para novos jogadores v2
            data["version"] = 2
            
        return data

# --- CAMADA DE PERSISTÊNCIA (Engine) ---
class SaveSystem:
    """Subsistema desacoplado de serialização e escrita."""
    
    def __init__(self, migration_manager: MigrationManager):
        self.migration_manager = migration_manager

    def serialize(self, state: PlayerState) -> str:
        payload = {
            "version": 2,
            "data": {
                "name": state.name,
                "health": state.health,
                "stamina": state.stamina
            }
        }
        json_data = json.dumps(payload)
        checksum = hashlib.md5(json_data.encode()).hexdigest()
        return json.dumps({"payload": json_data, "checksum": checksum})

    def deserialize(self, raw_save: str) -> (PlayerState, float):
        start_time = time.perf_counter()
        
        envelope = json.loads(raw_save)
        payload_str = envelope["payload"]
        expected_checksum = envelope["checksum"]
        
        # 1. Validação de Integridade
        actual_checksum = hashlib.md5(payload_str.encode()).hexdigest()
        if actual_checksum != expected_checksum:
            raise ValueError("CORRUPÇÃO DETECTADA: Checksum não confere!")

        # 2. Parsing do Payload
        data = json.loads(payload_str)
        
        # 3. Migração de Versão
        migrated_data = self.migration_manager.migrate(data)
        
        # 4. Reconstrução do Objeto de Domínio
        game_data = migrated_data["data"]
        state = PlayerState(
            name=game_data["name"],
            health=game_data["health"],
            stamina=game_data["stamina"]
        )
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        return state, duration_ms

# --- TESTE DE CAMPO (Experimento) ---
def run_experiment():
    migrator = MigrationManager()
    save_system = SaveSystem(migrator)

    print("--- TESTE 1: Salvamento e Carga v2 (Fluxo Normal) ---")
    original_player = PlayerState("Hero", 80, 50)
    save_file = save_system.serialize(original_player)
    
    loaded_player, duration = save_system.deserialize(save_file)
    
    assert loaded_player == original_player, "Erro: Dados carregados não batem com originais!"
    assert duration < 150, f"Erro: Tempo de restauração muito alto: {duration}ms"
    print(f"SUCESSO: Integridade e Performance validadas ({duration:.4f}ms).\n")

    print("--- TESTE 2: Migração de v1 para v2 (Cenário de Update) ---")
    v1_payload = json.dumps({
        "version": 1,
        "data": {"name": "OldHero", "health": 50}
    })
    v1_checksum = hashlib.md5(v1_payload.encode()).hexdigest()
    v1_save_file = json.dumps({"payload": v1_payload, "checksum": v1_checksum})

    loaded_v1_player, duration_v1 = save_system.deserialize(v1_save_file)
    
    assert loaded_v1_player.name == "OldHero"
    assert loaded_v1_player.stamina == 100, f"Erro: Migração falhou! Stamina esperada 100, obtida {loaded_v1_player.stamina}"
    print(f"SUCESSO: Migração de schema v1 -> v2 realizada ({duration_v1:.4f}ms).\n")

    print("--- TESTE 3: Detecção de Corrupção ---")
    corrupted_save = save_file.replace("Hero", "Villain") 
    try:
        save_system.deserialize(corrupted_save)
        print("ERRO: O sistema aceitou um arquivo corrompido!")
        exit(1)
    except ValueError as e:
        print(f"SUCESSO: Corrupção detectada corretamente: {e}")

if __name__ == "__main__":
    run_experiment()