import json
import sys

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("Erro: A biblioteca 'jsonschema' não está instalada.")
    sys.exit(1)

class SchemaRegistry:
    def __init__(self):
        self.schemas = {}

    def register(self, subject, schema):
        if subject not in self.schemas:
            self.schemas[subject] = []
        
        if self.schemas[subject]:
            latest_schema = self.schemas[subject][-1]
            if not self._is_backward_compatible(latest_schema, schema):
                return False, "Incompatibilidade: O novo schema quebra contratos da versão anterior (remoção de campo ou mudança de tipo)."
        
        self.schemas.append(schema) if isinstance(self.schemas, list) else self.schemas[subject].append(schema)
        return True, "Registrado com sucesso"

    def _is_backward_compatible(self, old, new):
        old_props = old.get("properties", {})
        new_props = new.get("properties", {})
        
        # 1. Regra de Backward: Nenhum campo existente na versão anterior pode ser removido
        for field in old_props:
            if field not in new_props:
                return False # Campo obrigatório ou opcional antigo foi removido
            
            # 2. Regra de Backward: O tipo de um campo existente não pode mudar
            old_type = old_props[field].get("type")
            new_type = new_props[field].get("type")
            if old_type and new_type and old_type != new_type:
                return False

        return True

    def validate_payload(self, subject, version, payload):
        schema = self.schemas[subject][version - 1]
        try:
            validate(instance=payload, schema=schema)
            return True, "Valid"
        except ValidationError as e:
            return False, e.message

# --- Testando os Cenários ---
registry = SchemaRegistry()

# Schema v1 base
schema_v1 = {
    "type": "object", 
    "properties": {
        "id": {"type": "integer"}, 
        "name": {"type": "string"}
    }, 
    "required": ["id", "name"]
}
registry.register("user-service", schema_v1)

# Cenário A: Tentativa de registrar v2 removendo campo 'name' (Deve ser REJEITADO)
schema_v2_broken = {
    "type": "object", 
    "properties": {
        "id": {"type": "integer"}
    }, 
    "required": ["id"]
}
success_v2, msg_v2 = registry.register("user-service", schema_v2_broken)
print(f"Cenário Remoção de Campo - Resultado: {success_v2}, Mensagem: {msg_v2}")
assert success_v2 == False

# Cenário B: Mudança adversarial de tipo de dado (ex: 'id' de integer para string - Deve ser REJEITADO)
schema_v2_type_change = {
    "type": "object", 
    "properties": {
        "id": {"type": "string"}, 
        "name": {"type": "string"}
    }, 
    "required": ["id", "name"]
}
success_type, msg_type = registry.register("user-service", schema_v2_type_change)
print(f"Cenário Mudança de Tipo - Resultado: {success_type}, Mensagem: {msg_type}")
assert success_type == False

print("Todos os testes de restrição de compatibilidade passaram com sucesso!")