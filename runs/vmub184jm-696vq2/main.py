import json
import time
from typing import Dict, Any, List, Tuple

# ==========================================
# 1. MODELOS DE DOMÍNIO E DTOS
# ==========================================

class Entity:
    def __init__(self, entity_id: int, name: str, health: int, max_health: int, position: Tuple[float, float]):
        self.entity_id = entity_id
        self.name = name
        self.health = health
        self.max_health = max_health # Introduzido na v2
        self.position = position     # v1: x, y separados -> v2: tupla (x, y)

# ==========================================
# 2. SISTEMA DE MIGRAÇÃO DE SCHEMA
# ==========================================

def migrate_save_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pipeline de migração incremental de schemas.
    Evolui os dados da versão encontrada até a versão atual (v2).
    """
    version = raw_data.get("version", 1)
    
    # Migração da v1 para v2
    if version == 1:
        print(f"[Migration] Migrando save da versão 1 para a versão 2...")
        for entity in raw_data.get("entities", []):
            # v1 guardava 'x' e 'y' separados na raiz ou dentro de transform
            x = entity.pop("x", 0.0)
            y = entity.pop("y", 0.0)
            entity["position"] = [x, y]
            
            # v1 não tinha max_health; inferimos da saúde atual ou definimos padrão
            entity["max_health"] = entity.get("health", 100)
            
        raw_data["version"] = 2
        version = 2

    # Futuras migrações entrariam aqui (ex: if version == 2: migrate_v2_to_v3(raw_data))
    return raw_data

# ==========================================
# 3. CAMADA DE PERSISTÊNCIA E SERIALIZAÇÃO
# ==========================================

CURRENT_SCHEMA_VERSION = 2

def serialize_game_state(entities: List[Entity]) -> str:
    """Serializa o estado do mundo em um payload JSON versionado."""
    state = {
        "version": CURRENT_SCHEMA_VERSION,
        "timestamp": time.time(),
        "entities": [
            {
                "id": e.entity_id,
                "name": e.name,
                "health": e.health,
                "max_health": e.max_health,
                "position": [e.position[0], e.position[1]]
            }
            for e in entities
        ]
    }
    return json.dumps(state)

def deserialize_game_state(json_str: str) -> List[Entity]:
    """Desserializa, aplica migração e converte para objetos de domínio."""
    try:
        raw_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Save corrompido: JSON inválido. Detalhes: {e}")
        
    if "version" not in raw_data or "entities" not in raw_data:
        raise ValueError("Save corrompido: Estrutura básica ausente (version/entities).")

    # Aplica migração de schema se necessário
    migrated_data = migrate_save_data(raw_data)
    
    entities = []
    for item in migrated_data["entities"]:
        pos = item.get("position", [0.0, 0.0])
        entity = Entity(
            entity_id=item["id"],
            name=item["name"],
            health=item["health"],
            max_health=item.get("max_health", 100),
            position=(pos[0], pos[1])
        )
        entities.append(entity)
        
    return entities

# ==========================================
# 4. EXECUÇÃO E TESTES DE VALIDAÇÃO
# =================5=========================

def run_experiment():
    print("=== INICIANDO PIPELINE DE SAVE/LOAD ===")
    
    # 1. Gerar carga de 10.000 entidades
    num_entities = 10000
    print(f"Gerando {num_entities} entidades ativas...")
    original_entities = [
        Entity(
            entity_id=i,
            name=f"Unit_{i}",
            health=85,
            max_health=100,
            position=(float(i), float(i * 2))
        )
        for i in range(num_entities)
    ]
    
    # 2. Medir tempo de Serialização
    start_time = time.perf_counter()
    serialized_data = serialize_game_state(original_entities)
    serialize_duration = (time.perf_counter() - start_time) * 1000.0
    print(f"[{num_entities} Entidades] Tempo de Serialização: {serialize_duration:.2f} ms")
    
    # 3. Medir tempo de Desserialização (v2 -> v2)
    start_time = time.perf_counter()
    loaded_entities = deserialize_game_state(serialized_data)
    deserialize_duration = (time.perf_counter() - start_time) * 1000.0
    print(f"[{num_entities} Entidades] Tempo de Desserialização: {deserialize_duration:.2f} ms")
    
    # Validação do critério de performance (< 50ms)
    total_pipeline_time = serialize_duration + deserialize_duration
    print(f"Tempo total do pipeline (Save + Load): {total_pipeline_time:.2f} ms")
    assert total_pipeline_time < 50.0, f"Falha de Performance: Pipeline levou {total_pipeline_time:.2f}ms (limite: 50ms)"

    # 4. Validar Teste de Migração (Simulando um arquivo legado v1)
    print("\n--- TESTANDO MIGRAÇÃO DE SCHEMA (v1 para v2) ---")
    legacy_v1_payload = json.dumps({
        "version": 1,
        "entities": [
            {"id": 999, "name": "Hero_Legacy", "health": 50, "x": 10.5, "y": 20.0}
        ]
    })
    
    migrated_entities = deserialize_game_state(legacy_v1_payload)
    assert len(migrated_entities) == 1
    migrated_hero = migrated_entities[0]
    assert migrated_hero.max_health == 50 # Inferido corretamente pela migração
    assert migrated_hero.position == (10.5, 20.0) # Convertido de x,y para tupla
    print("Migração de v1 para v2 validada com sucesso! Nenhum dado corrompido.")

    # 5. Contraexemplo: Tratamento de Save Corrompido
    print("\n--- TESTANDO TRATAMENTO DE SAVE CORROMPIDO ---")
    corrupted_payload = "{ 'version': 2, 'entities': [ malformed json ... "
    try:
        deserialize_game_state(corrupted_payload)
    except ValueError as e:
        print(f"Exceção capturada com sucesso (Comportamento Esperado): {e}")

    print("\n[SUCESSO] Todos os testes do pipeline passaram com rigor absoluto!")

if __name__ == "__main__":
    run_experiment()