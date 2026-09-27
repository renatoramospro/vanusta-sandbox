import unittest

class SecureProjectionEngine:
    def __init__(self):
        # Armazena o estado simulado do Read Model por tenant e agregado
        self.read_models = {}
        self.dlq = []

    def process_event(self, tenant_id, aggregate_id, version, payload):
        key = f"{tenant_id}:{aggregate_id}"
        current_state = self.read_models.get(key, {"version": 0, "data": {}})
        current_version = current_state["version"]

        # 1. Idempotência: Se o evento já foi processado, rejeita/ignora
        if version <= current_version:
            return "IGNORED_DUPLICATE"

        # 2. Confiabilidade / Gap Detection: Se há salto de versão, vai para DLQ
        if version != current_version + 1:
            self.dlq.append({"tenant_id": tenant_id, "aggregate_id": aggregate_id, "version": version})
            return "SENT_TO_DLQ"

        # 3. Processamento bem-sucedido
        current_state["version"] = version
        current_state["data"].update(payload)
        self.read_models[key] = current_state
        return "SUCCESS"

class TestSecureProjection(unittest.TestCase):
    def test_idempotency_and_gaps(self):
        engine = SecureProjectionEngine()

        # Evento 1: Válido
        res1 = engine.process_event("tenant-A", "user-1", 1, {"name": "Alice"})
        self.assertEqual(res1, "SUCCESS")

        # Evento 1 duplicado (Idempotência)
        res_dup = engine.process_event("tenant-A", "user-1", 1, {"name": "Alice"})
        self.assertEqual(res_dup, "IGNORED_DUPLICATE")

        # Evento 3 com lacuna (Pula o 2) -> Deve ir para DLQ
        res_gap = engine.process_event("tenant-A", "user-1", 3, {"name": "Alice Admin"})
        self.assertEqual(res_gap, "SENT_TO_DLQ")
        self.assertEqual(len(engine.dlq), 1)

        # Evento 2 correto (Preenchendo a lacuna após tratamento/replay correto)
        res2 = engine.process_event("tenant-A", "user-1", 2, {"email": "alice@test.com"})
        self.assertEqual(res2, "SUCCESS")
        
        # Verifica estado final consolidado
        state = engine.read_models["tenant-A:user-1"]
        self.assertEqual(state["version"], 2)
        self.assertEqual(state["data"]["name"], "Alice")
        self.assertEqual(state["data"]["email"], "alice@test.com")
        print("Teste de segurança e idempotência executado com sucesso!")

if __name__ == "__main__":
    unittest.main()