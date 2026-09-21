import json
import time
from typing import Dict, Any, List, Tuple, Callable

# ==========================================
# 1. MODELOS DE DOMÍNIO (Game Logic)
# ==========================================

class Entity:
    """Representa a entidade no motor do jogo (Domínio)."""
    def __init__(self, entity_id: int, name: str, health: int, max_health: int, position: Tuple[float, float]):
        self.entity_id = entity_id
        self.name = name
        self.health = health
        self.max_health = max_health
        self.position = position

    def __repr__(self):
        return f"Entity({self.name}, HP: {self.health}/{self.max_health}, Pos: {self.position})"

# ==========================================
# 2. CAMADA DE VALIDAÇÃO SEMÂNTICA
# ==========================================

class SchemaValidator:
    """Garante que os dados não são apenas sintaticamente corretos, mas semanticamente válidos."""
    
    @staticmethod
    def validate_entity_data(data: Dict[str, Any]):
        # Regras de negócio aplicadas aos dados brutos
        if data.get("health", 0) < 0:
            raise ValueError(f"Erro Semântico: Entidade {data.get('id')} tem vida negativa ({data.get('health')}).")
        
        if isinstance(data.get("position"), list):
            if len(data["position"]) != 2:
                raise ValueError("Erro Semântico: Posição deve ter exatamente 2 coordenadas (x, y).")
            if not all(isinstance(c, (int, float)) for c in data["position"]):
                raise ValueError("Erro Semântico: Coordenadas devem ser numéricas.")

# ==========================================
# 3. PIPELINE DE MIGRAÇÃO ENCADEÁVEL
# ==========================================

class MigrationRegistry:
    """Gerencia a evolução do schema de forma incremental (v1 -> v2 -> v3...)."""
    def __init__(self):
        # Mapeia a versão de origem para a função que a transforma na próxima versão
        self._migrations: Dict[int, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    def register(self, from_version: int, func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self._migrations[from_version] = func

    def migrate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        current_version = data.get("version", 1)
        
        # Enquanto houver uma migração registrada para a versão atual, aplica-a
        while current_version in self._migrations:
            print(f"[Migration] Aplicando migração de v{current_version} para v{current_version + 1}...")
            data = self._migrations[current_version](data)
            current_version = data.get("version")
            
        return data

# Definição das funções de migração (Lógica de transformação)
def migrate_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
    """v1: x, y separados | v2: position é tupla, adiciona max_health."""
    new_entities = []
    for ent in data["entities"]:
        new_ent = ent.copy()
        # Transforma x, y em tupla
        new_ent["position"] = (ent["x"], ent["y"])
        # Remove campos antigos
        del new_ent["x"]
        del new_ent["y"]
        # Infere max_health (regra de negócio da migração)
        new_ent["max_health"] = ent["health"]
        new_entities.append(new_ent)
    
    return {"version": 2, "entities": new_entities}

def migrate_v2_to_v3(data: Dict[str, Any]) -> Dict[str, Any]:
    """v2: status normal | v3: adiciona campo 'is_active'."""
    for ent in data["entities"]:
        ent["is_active"] = True
    return {"version": 3, "entities": data["entities"]}

# ==========================================
# 4. CORE: SERIALIZAÇÃO E PERSISTÊNCIA
# ==========================================

class SaveSystem:
    def __init__(self, migration_registry: MigrationRegistry):
        self.migration_registry = migration_registry
        self.validator = SchemaValidator()

    def serialize(self, entities: List[Entity]) -> str:
        """Transforma entidades de domínio em DTOs JSON."""
        dto_list = []
        for e in entities:
            dto_list.append({
                "id": e.entity_id,
                "name": e.name,
                "health": e.health,
                "max_health": e.max_health,
                "position": e.position,
                "is_active": True # Campo da v3
            })
        payload = {"version": 3, "entities": dto_list}
        return json.dumps(payload)

    def deserialize(self, raw_json: str) -> List[Entity]:
        """Carrega, migra, valida e reconstrói o estado de domínio."""
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Save corrompido: JSON inválido. Detalhes: {e}")

        # 1. Migração Encadeada
        data = self.migration_registry.migrate(data)

        # 2. Validação Semântica
        for ent_data in data["entities"]:
            self.validator.validate_entity_data(ent_data)

        # 3. Mapeamento para Domínio
        entities = []
        for d in data["entities"]:
            entities.append(Entity(
                entity_id=d["id"],
                name=d["name"],
                health=d["health"],
                max_health=d["max_health"],
                position=tuple(d["position"])
            ))
        return entities

# ==========================================
# 5. EXPERIMENTO E TESTES
# ==========================================

def run_experiment():
    # Setup
    registry = MigrationRegistry()
    registry.register(1, migrate_v1_to_v2)
    registry.register(2, migrate_v2_to_v3)
    save_system = SaveSystem(registry)

    print("=== INICIANDO PIPELINE DE SAVE/LOAD (CORRIGIDO) ===\n")

    # --- TESTE 1: Performance (10.000 entidades) ---
    print("--- TESTE 1: Performance (10k entidades) ---")
    entities = [Entity(i, f"NPC_{i}", 100, 100, (float(i), float(i))) for i in range(10000)]
    
    start_ser = time.perf_counter()
    json_data = save_system.serialize(entities)
    ser_time = (time.perf_counter() - start_ser) * 1000

    start_des = time.perf_counter()
    loaded_entities = save_system.deserialize(json_data)
    des_time = (time.perf_counter() - start_des) * 1000

    print(f"Serialização: {ser_time:.2f}ms | Desserialização: {des_time:.2f}ms")
    print(f"Total: {ser_time + des_time:.2f}ms")
    assert (ser_time + des_time) < 50.0, "FALHA: Performance acima de 50ms"

    # --- TESTE 2: Migração Encadeada (v1 -> v3) ---
    print("\n--- TESTE 2: Migração Encadeada (v1 -> v3) ---")
    v1_payload = json.dumps({
        "version": 1,
        "entities": [{"id": 1, "name": "OldHero", "health": 80, "x": 10.0, "y": 20.0}]
    })
    migrated_entities = save_system.deserialize(v1_payload)
    hero = migrated_entities[0]
    assert hero.max_health == 80, "Migração v1->v2 falhou (max_health)"
    assert hero.position == (10.0, 20.0), "Migração v1->v2 falhou (position)"
    print(f"Sucesso: {hero}")

    # --- TESTE 3: Validação Semântica (Dados Inválidos) ---
    print("\n--- TESTE 3: Validação Semântica (Vida Negativa) ---")
    bad_data = json.dumps({
        "version": 3,
        "entities": [{"id": 2, "name": "Ghost", "health": -10, "max_health": 100, "position": [0, 0]}]
    })
    try:
        save_system.deserialize(bad_data)
    except ValueError as e:
        print(f"Capturado erro semântico esperado: {e}")
        assert "vida negativa" in str(e)

    # --- TESTE 4: Corrupção de Sintaxe ---
    print("\n--- TESTE 4: Corrupção de Sintaxe (JSON quebrado) ---")
    broken_json = "{ 'version': 3, 'entities': [ "
    try:
        save_system.deserialize(broken_json)
    except ValueError as e:
        print(f"Capturado erro de sintaxe esperado: {e}")
        assert "JSON inválido" in str(e)

    print("\n[RESULTADO FINAL] Todos os testes passaram com sucesso!")

if __name__ == "__main__":
    run_experiment()