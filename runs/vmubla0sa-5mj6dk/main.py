import hashlib
import time

class FeatureFlagEngine:
    def __init__(self):
        # Cache local: O estado real estaria em memória, atualizado via API/Eventos
        self._flags = {
            "nova_ui": {
                "enabled": True,
                "rollout": 50,
                "rules": {"tier": "premium"}
            }
        }

    def _get_hash(self, user_id, flag_key):
        # Hashing determinístico para garantir consistência do usuário
        val = f"{user_id}:{flag_key}".encode()
        return int(hashlib.md5(val).hexdigest(), 16) % 100

    def is_enabled(self, flag_key, user_context):
        flag = self._flags.get(flag_key)
        if not flag or not flag["enabled"]:
            return False
        
        # 1. Avaliação de Atributos (Regras)
        for attr, value in flag.get("rules", {}).items():
            if user_context.get(attr) != value:
                return False
        
        # 2. Avaliação de Rollout (Percentual)
        user_id = user_context.get("id")
        if user_id and self._get_hash(user_id, flag_key) >= flag["rollout"]:
            return False
            
        return True

# Teste de performance e consistência
engine = FeatureFlagEngine()
user_a = {"id": "user_123", "tier": "premium"}

# Medição de latência
start = time.perf_counter()
result = engine.is_enabled("nova_ui", user_a)
end = time.perf_counter()

print(f"Resultado: {result}")
print(f"Latência: {(end - start) * 1000:.4f}ms")

# Contraexemplo: Usuário não-premium falhando na regra
user_b = {"id": "user_456", "tier": "free"}
assert engine.is_enabled("nova_ui", user_b) == False
print("Contraexemplo (Regra de Atributo) validado com sucesso.")