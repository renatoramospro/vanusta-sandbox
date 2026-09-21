import json
import jsonschema
from jsonschema import validate, ValidationError

# Simulação de um Schema Registry simples
class SchemaRegistry:
    def __init__(self):
        self.schemas = {}

    def register(self, subject, schema):
        # Em um cenário real, aqui aplicaríamos a lógica de compatibilidade
        # antes de salvar a nova versão.
        if subject not in self.schemas:
            self.schemas[subject] = []
        self.schemas[subject].append(schema)
        return len(self.schemas[subject])

    def validate_payload(self, subject, version, payload):
        schema = self.schemas[subject][version - 1]
        try:
            validate(instance=payload, schema=schema)
            return True, "Valid"
        except ValidationError as e:
            return False, e.message

# Experimento
registry = SchemaRegistry()

# 1. Definindo um Schema (v1)
schema_v1 = {
    "type": "object",
    "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
    "required": ["id", "name"]
}

registry.register("user-service", schema_v1)

# 2. Testando validação com sucesso
payload_ok = {"id": 1, "name": "Vanusta"}
is_valid, msg = registry.validate_payload("user-service", 1, payload_ok)
print(f"Validação v1 (sucesso): {is_valid}, {msg}")

# 3. Testando falha (Equívoco comum: enviar tipo errado)
payload_fail = {"id": "um", "name": "Vanusta"}
is_valid, msg = registry.validate_payload("user-service", 1, payload_fail)
print(f"Validação v1 (falha esperada): {is_valid}, Erro: {msg[:30]}...")

# 4. Demonstração de quebra de contrato (Equívoco: remover campo obrigatório)
# Se a v2 remover 'name', consumidores da v1 quebrarão.
schema_v2 = {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}
registry.register("user-service", schema_v2)

# O consumidor da v1 espera 'name', mas se o produtor evoluir para v2, 
# o contrato foi quebrado se não houver compatibilidade.
print("Conclusão: O registro deve impedir o registro de schema_v2 se a política for Backward.")