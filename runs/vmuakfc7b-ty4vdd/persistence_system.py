import json
import time
import hashlib
import hmac
import os

# --- CONFIGURAÇÃO DE SEGURANÇA ---
SECRET_KEY = b"super-secret-game-key-123"
MAX_SAVE_SIZE_BYTES = 1024 * 1024  # Limite de 1MB para evitar DoS
SAFE_SAVE_DIR = os.path.abspath("saves")

# --- CAMADA DE DOMÍNIO ---
class PlayerState:
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

# --- CAMADA DE EVOLUÇÃO ---
class MigrationManager:
    def __init__(self, target_version: int):
        self.target_version = target_version
        self._migrations = {
            1: self._migrate_v1_to_v2,
            2: self._migrate_v2_to_v3
        }

    def _migrate_v1_to_v2(self, data: dict) -> dict:
        data["stamina"] = 100
        data["version"] = 2
        return data

    def _migrate_v2_to_v3(self, data: dict) -> dict:
        data["mana"] = 50
        data["version"] = 3
        return data

    def migrate(self, data: dict) -> dict:
        current_v = data.get("version", 1)
        while current_v < self.target_version:
            if current_v not in self._migrations:
                raise ValueError(f"Sem migrador para v{current_v}")
            data = self._migrations[current_v](data)
            current_v = data["version"]
        return data

# --- CAMADA DE PERSISTÊNCIA (CORRIGIDA) ---
class SaveSystem:
    def __init__(self, migration_manager: MigrationManager):
        self.migration_manager = migration_manager

    def _generate_hmac(self, payload: str) -> str:
        """Gera HMAC-SHA256 para integridade e autenticidade."""
        return hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()

    def _get_safe_path(self, filename: str) -> str:
        """Evita Path Traversal sanitizando o nome do arquivo."""
        base_name = os.path.basename(filename)
        return os.path.join(SAFE_SAVE_DIR, base_name)

    def save(self, filename: str, state: PlayerState):
        if not os.path.exists(SAFE_SAVE_DIR):
            os.makedirs(SAFE_SAVE_DIR)
            
        path = self._get_safe_path(filename)
        payload_dict = {
            "name": state.name,
            "health": state.health,
            "stamina": state.stamina,
            "mana": state.mana,
            "version": 3
        }
        payload_str = json.dumps(payload_dict)
        signature = self._generate_hmac(payload_str)
        
        full_data = {
            "payload": payload_str,
            "signature": signature
        }
        
        with open(path, "w") as f:
            json.dump(full_data, f)

    def deserialize(self, filename: str) -> tuple[PlayerState, float]:
        start_time = time.perf_counter()
        path = self._get_safe_path(filename)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Save {filename} não encontrado.")

        # 1. Proteção contra DoS: Verificar tamanho do arquivo antes de ler
        if os.path.getsize(path) > MAX_SAVE_SIZE_BYTES:
            raise ValueError("Arquivo de save excessivamente grande (DoS Risk).")

        with open(path, "r") as f:
            container = json.load(f)

        payload_str = container["payload"]
        signature = container["signature"]

        # 2. Proteção contra Manipulação (Anti-Cheat): Validar HMAC
        if not hmac.compare_digest(self._generate_hmac(payload_str), signature):
            raise PermissionError("Assinatura inválida! O arquivo foi alterado ou corrompido.")

        # 3. Parsing e Migração
        try:
            data = json.loads(payload_str)
        except json.JSONDecodeError:
            raise ValueError("ERRO: JSON malformado.")

        migrated_data = self.migration_manager.migrate(data)

        # 4. Validação de Tipos (Integridade de Domínio)
        try:
            state = PlayerState(
                name=str(migrated_data["name"]),
                health=int(migrated_data["health"]),
                stamina=int(migrated_data["stamina"]),
                mana=int(migrated_data["mana"])
            )
        except (KeyError, ValueError, TypeError) as e:
            raise TypeError(f"ERRO: Falha na integridade de tipos após migração: {e}")

        duration = (time.perf_counter() - start_time) * 1000
        return state, duration

# --- EXPERIMENTO DE SEGURANÇA ---
def run_experiment():
    os.makedirs(SAFE_SAVE_DIR, exist_ok=True)
    mm = MigrationManager(target_version=3)
    ss = SaveSystem(mm)

    print("--- TESTE 1: Fluxo Seguro (HMAC + Migração) ---")
    # Criando um save v1 manual para testar migração + segurança
    v1_payload = json.dumps({"name": "OldHero", "health": 80, "version": 1})
    v1_signature = hmac.new(SECRET_KEY, v1_payload.encode(), hashlib.sha256).hexdigest()
    
    v1_file_path = os.path.join(SAFE_SAVE_DIR, "v1_save.json")
    with open(v1_file_path, "w") as f:
        json.dump({"payload": v1_payload, "signature": v1_signature}, f)

    state, dur = ss.deserialize("v1_save.json")
    print(f"SUCESSO: {state} restaurado em {dur:.4f}ms")

    print("\n--- TESTE 2: Ataque de Manipulação (Anti-Cheat) ---")
    # Tentando alterar o health no payload sem atualizar a assinatura
    with open(v1_file_path, "r") as f:
        corrupt_container = json.load(f)
    
    # Alterando o valor no JSON mas mantendo a assinatura antiga
    corrupt_payload = json.loads(corrupt_container["payload"])
    corrupt_payload["health"] = 999
    corrupt_container["payload"] = json.dumps(corrupt_payload)

    with open(v1_file_path, "w") as f:
        json.dump(corrupt_container, f)

    try:
        ss.deserialize("v1_save.json")
        print("ERRO: O sistema aceitou um save manipulado!")
        exit(1)
    except PermissionError as e:
        print(f"SUCESSO: Bloqueado ataque de manipulação: {e}")

    print("\n--- TESTE 3: Ataque de Path Traversal ---")
    try:
        ss.deserialize("../../../etc/passwd")
        print("ERRO: O sistema permitiu acesso fora do diretório seguro!")
        exit(1)
    except Exception as e:
        # O os.path.basename deve transformar o caminho em "passwd" e procurar em saves/passwd
        print(f"SUCESSO: Tentativa de Path Traversal neutralizada. Tentou acessar: {e}")

    print("\n--- TESTE 4: Proteção contra DoS (Tamanho) ---")
    dos_file = os.path.join(SAFE_SAVE_DIR, "dos.json")
    with open(dos_file, "wb") as f:
        f.write(b"A" * (MAX_SAVE_SIZE_BYTES + 100))
    
    try:
        ss.deserialize("dos.json")
        print("ERRO: O sistema aceitou um arquivo gigante!")
        exit(1)
    except ValueError as e:
        print(f"SUCESSO: Bloqueado ataque de DoS: {e}")

if __name__ == "__main__":
    run_experiment()