import json
import time
import hashlib
from typing import Dict, Any, Callable

# --- CAMADA DE DOMÍNIO (Estado do Jogo) ---
class PlayerState:
    """Representa o estado atual do jogador (v3)."""
    def __init__(self, name: str, health: int, stamina: int, mana: int):
        self.name = name
        self.health = health
        self.stamina = stamina
        self.mana = mana

    def __eq__(self, other):
        if not isinstance(other, PlayerState): return False
        return (self.name == other.name and self.health == other.health and 
                self.stamina == other.stamina and self.mana == other.mana)

    def __repr__(self):
        return f"PlayerState(name='{self.name}', health={self.health}, stamina={self.stamina}, mana={self.mana})"

# --- CAMADA DE EVOLUÇÃO (Migração Incremental) ---
class MigrationManager:
    """Gerencia a evolução de schemas através de uma cadeia de transformações."""
    
    def __init__(self, target_version: int):
        self.target_version = target_version
        # Mapeia: versão_origem -> função_de_transformação
        self._migrations: Dict[int, Callable[[Dict], Dict]] = {
            1: self._migrate_v1_to_v2,
            2: self._migrate_v2_to_v3
        }

    def _migrate_v1_to_v2(self, data: Dict) -> Dict:
        print("[Migration] Aplicando v1 -> v2 (Adicionando stamina)")
        data["stamina"] = 100
        data["version"] = 2
        return data

    def _migrate_v2_to_v3(self, data: Dict) -> Dict:
        print("[Migration] Aplicando v2 -> v3 (Adicionando mana)")
        data["mana"] = 50
        data["version"] = 3
        return data

    def migrate(self, data: Dict) -> Dict:
        current_version = data.get("version", 1)
        
        while current_version < self.target_version:
            migration_func = self._migrations.get(current_version)
            if not migration_func:
                raise RuntimeError(f"Sem migrador definido para versão {current_version}")
            
            data = migration_func(data)
            current_version = data.get("version")
            
        return data

# --- CAMADA DE PERSISTÊNCIA ---
class SaveSystem:
    def __init__(self, migration_manager: MigrationManager):
        self.migration_manager = migration_manager

    def _generate_checksum(self, data_str: str) -> str:
        return hashlib.md5(data_str.encode()).hexdigest()

    def serialize(self, player: PlayerState) -> str:
        payload = {
            "name": player.name,
            "health": player.health,
            "stamina": player.stamina,
            "mana": player.mana,
            "version": self.migration_manager.target_version
        }
        payload_str = json.dumps(payload)
        checksum = self._generate_checksum(payload_str)
        return json.dumps({"payload": payload, "checksum": checksum})

    def deserialize(self, raw_json: str) -> PlayerState:
        # 1. Parsing Seguro
        try:
            envelope = json.loads(raw_json)
        except json.JSONDecodeError:
            raise ValueError("ERRO: JSON malformado.")

        payload = envelope.get("payload")
        checksum_received = envelope.get("checksum")

        # 2. Validação de Integridade
        payload_str = json.dumps(payload)
        if self._generate_checksum(payload_str) != checksum_received:
            raise ValueError("ERRO: Checksum inválido! Arquivo corrompido.")

        # 3. Migração em Cadeia
        migrated_payload = self.migration_manager.migrate(payload)

        # 4. Instanciação com validação de tipos básica
        try:
            return PlayerState(
                name=str(migrated_payload["name"]),
                health=int(migrated_payload["health"]),
                stamina=int(migrated_payload["stamina"]),
                mana=int(migrated_payload["mana"])
            )
        except (KeyError, TypeError, ValueError) as e:
            raise TypeError(f"ERRO: Falha na integridade de tipos após migração: {e}")

# --- EXPERIMENTO ---
def run_experiment():
    target_v = 3
    migrator = MigrationManager(target_v)
    save_system = SaveSystem(migrator)

    print("--- TESTE 1: Migração em Cadeia (v1 -> v3) ---")
    # Simulando um save muito antigo (v1)
    v1_data = {
        "payload": {"name": "OldHero", "health": 80, "version": 1},
        "checksum": "" 
    }
    # Gerar checksum correto para o v1_data
    v1_payload_str = json.dumps(v1_data["payload"])
    v1_data["checksum"] = hashlib.md5(v1_payload_str.encode()).hexdigest()
    v1_save_file = json.dumps(v1_data)

    start_time = time.time()
    player = save_system.deserialize(v1_save_file)
    duration = (time.time() - start_time) * 1000

    print(f"Objeto restaurado: {player}")
    assert player.stamina == 100, "Falha: Stamina (v2) não migrada"
    assert player.mana == 50, "Falha: Mana (v3) não migrada"
    assert duration < 150, f"Performance falhou: {duration}ms"
    print(f"SUCESSO: Migração v1->v3 concluída em {duration:.4f}ms.")

    print("\n--- TESTE 2: Resiliência a JSON Malformado ---")
    try:
        save_system.deserialize("{ 'invalid_json': True ")
        print("ERRO: O sistema não detectou JSON malformado!")
        exit(1)
    except ValueError as e:
        print(f"SUCESSO: Capturado erro de parsing: {e}")

    print("\n--- TESTE 3: Resiliência a Corrupção de Tipo ---")
    # v2 que tem 'health' como string, mas o domínio v3 exige int
    v2_corrupt_data = {
        "payload": {"name": "Glitch", "health": "muito_alto", "stamina": 100, "version": 2},
        "checksum": ""
    }
    v2_payload_str = json.dumps(v2_corrupt_data["payload"])
    v2_corrupt_data["checksum"] = hashlib.md5(v2_payload_str.encode()).hexdigest()
    
    try:
        save_system.deserialize(json.dumps(v2_corrupt_data))
        print("ERRO: O sistema aceitou tipo de dado inválido!")
        exit(1)
    except TypeError as e:
        print(f"SUCESSO: Capturado erro de tipo: {e}")

if __name__ == "__main__":
    run_experiment()