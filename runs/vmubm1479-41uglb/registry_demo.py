import json
import sys

# Tentativa de importação com tratamento para garantir que o ambiente rode
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
        
        # Lógica de Compatibilidade (Simulação de Backward Compatibility)
        if self.schemas[subject]:
            latest_schema = self.schemas[subject][-1]
            if not self._is_backward_compatible(latest_schema, schema):
                return False, "Incompatibilidade: O novo schema quebra consumidores da versão anterior."
        
        self.schemas[subject].append(schema)
        return True, "Registrado com sucesso"

    def _is_backward_compatible(self, old, new):
        # Regra simplificada: se campos obrigatórios foram removidos, é incompatível
        old_required = set(old.get("required", []))
        new_required = set(new.get("required", []))
        return new_required.issubset(old_required)

    def validate_payload(self, subject, version, payload):
        schema = self.schemas[subject][version - 1]
        try:
            validate(instance=payload, schema=schema)
            return True, "Valid"
        except ValidationError as e:
            return False, e.message

# Experimento
registry = SchemaRegistry()
schema_v1 = {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}, "required": ["id", "name"]}
registry.register("user-service", schema_v1)

# Tentativa de registrar v2 quebrando a compatibilidade (removendo 'name')
schema_v2_broken = {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}
success, msg = registry.register("user-service", schema_v2_broken)

print(f"Resultado do registro v2: {success}, {msg}")
assert success == False
print("Experimento concluído com sucesso: O registro impediu a quebra de contrato.")