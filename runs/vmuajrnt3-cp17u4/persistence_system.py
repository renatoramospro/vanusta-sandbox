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

    def __repr__(self):
        return f"PlayerState(name='{self.name}', health={self.health}, stamina={self.stamina})"

# --- CAMADA DE EVOLUÇÃO (Migração) ---
class MigrationManager:
    """Gerencia a transição de schemas entre versões."""
    
    @staticmethod
    def migrate(data: dict) -> dict:
        version = data.get("version", 1)
        
        # Se o dado é v1, precisamos transformá-lo em v2
        if version == 1:
            print(f"[Migration] Migrando schema v1 para v2...")
            # Regra de negócio da migração: v1 não tinha stamina. 
            # Definimos um valor padrão de 100 para novos jogadores migrados.
            data["stamina"] = 100
            data["version"] = 2
            
        return data

# --- CAMADA DE PERSISTÊNCIA (Mecanismo de Serialização) ---
class SaveSystem:
    """Responsável por serializar, deserializar e validar integridade."""
    
    def __init__(self, migration_manager: MigrationManager):
        self.migration_manager = migration_manager

    def _generate_checksum(self, data_str: str) -> str:
        return hashlib.md5(data_str.encode()).hexdigest()

    def serialize(self, player: PlayerState, version: int = 2) -> str:
        """Transforma o objeto em uma string JSON com envelope de metadados."""
        payload = {
            "name": player.name,
            "health": player.health,
            "stamina": player.stamina,
            "version": version
        }
        payload_str = json.dumps(payload, sort_keys=True)
        checksum = self._generate_checksum(payload_str)
        
        envelope = {
            "payload": payload,
            "checksum": checksum
        }
        return json.dumps(envelope)

    def deserialize(self, json_data: str) -> (PlayerState, float):
        """Restaura o objeto, aplicando migração e validando checksum."""
        start_time = time.perf_counter()
        
        envelope = json.loads(json_data)
        payload = envelope["payload"]
        stored_checksum = envelope["checksum"]
        
        # 1. Validação de Integridade (Checksum)
        # Re-geramos o hash do payload para comparar com o armazenado
        payload_str = json.dumps(payload, sort_keys=True)
        if self._generate_checksum(payload_str) != stored_checksum:
            raise ValueError("ERRO: Checksum inválido! O arquivo de save está corrompido.")

        # 2. Migração de Schema (O ponto crítico corrigido)
        # O payload é transformado ANTES de tentar instanciar o PlayerState
        migrated_payload = self.migration_manager.migrate(payload)

        # 3. Instanciação do Domínio
        # Agora garantimos que 'stamina' existe porque a migração a injetou
        player = PlayerState(
            name=migrated_payload["name"],
            health=migrated_payload["health"],
            stamina=migrated_payload["stamina"]
        )
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        return player, duration_ms

# --- EXPERIMENTO DE VALIDAÇÃO ---
def run_experiment():
    migration_mgr = MigrationManager()
    save_system = SaveSystem(migration_mgr)

    print("--- TESTE 1: Salvamento e Carga v2 (Fluxo Normal) ---")
    hero = PlayerState("Hero", 100, 50)
    v2_save_file = save_system.serialize(hero)
    
    loaded_hero, duration = save_system.deserialize(v2_save_file)
    
    assert loaded_hero == hero, f"Falha: {loaded_hero} != {hero}"
    print(f"SUCESSO: Integridade e Performance validadas ({duration:.4f}ms).")

    print("\n--- TESTE 2: Migração de v1 para v2 (Cenário de Update) ---")
    # Simulando um arquivo v1 manual (sem o campo stamina e versão 1)
    v1_payload = {"name": "OldHero", "health": 80, "version": 1}
    v1_payload_str = json.dumps(v1_payload, sort_keys=True)
    v1_checksum = hashlib.md5(v1_payload_str.encode()).hexdigest()
    v1_save_file = json.dumps({"payload": v1_payload, "checksum": v1_checksum})

    loaded_v1_player, duration_v1 = save_system.deserialize(v1_save_file)
    
    # Validações da migração
    assert loaded_v1_player.name == "OldHero"
    assert loaded_v1_player.health == 80
    assert loaded_v1_player.stamina == 100, f"Erro: Stamina não injetada! Obtida: {loaded_v1_player.stamina}"
    print(f"SUCESSO: Migração de schema v1 -> v2 realizada ({duration_v1:.4f}ms).")
    print(f"Objeto restaurado: {loaded_v1_player}")

    print("\n--- TESTE 3: Detecção de Corrupção ---")
    # Alteramos o nome no payload sem atualizar o checksum
    corrupted_data = json.loads(v2_save_file)
    corrupted_data["payload"]["name"] = "Villain"
    corrupted_save_file = json.dumps(corrupted_data)
    
    try:
        save_system.deserialize(corrupted_save_file)
        print("ERRO: O sistema aceitou um arquivo corrompido!")
        exit(1)
    except ValueError as e:
        print(f"SUCESSO: Corrupção detectada corretamente: {e}")

if __name__ == "__main__":
    run_experiment()