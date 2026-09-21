import hashlib

class FeatureFlagEngine:
    def __init__(self):
        self._flags = {
            "nova_ui": {
                "enabled": True,
                "rollout": 50,
                "rules": {"tier": "premium"}
            }
        }

    def _get_hash(self, user_id, flag_key):
        val = f"{user_id}:{flag_key}".encode()
        return int(hashlib.md5(val).hexdigest(), 16) % 100

    def is_enabled(self, flag_key, user_context):
        flag = self._flags.get(flag_key)
        if not flag or not flag["enabled"]:
            return False
        
        # 1. Avaliação de Atributos (Regras)
        # Correção: Verificar se a chave existe no contexto antes de comparar
        for attr, expected_value in flag.get("rules", {}).items():
            if attr not in user_context or user_context[attr] != expected_value:
                return False
        
        # 2. Avaliação de Rollout (Percentual)
        # Correção: Usuários sem ID não devem burlar o rollout. 
        # Se o ID é obrigatório para o rollout, tratamos como False ou usamos um fallback.
        user_id = user_context.get("id")
        if not user_id:
            return False # Usuários anônimos não entram no rollout
            
        if self._get_hash(user_id, flag_key) >= flag["rollout"]:
            return False
            
        return True

# Testes de Validação
engine = FeatureFlagEngine()

# Caso 1: Usuário sem ID (deve ser False)
assert engine.is_enabled("nova_ui", {"tier": "premium"}) == False
print("Sucesso: Usuário sem ID bloqueado no rollout.")

# Caso 2: Chave ausente no contexto (deve ser False, não None == valor)
assert engine.is_enabled("nova_ui", {"id": "user_123"}) == False
print("Sucesso: Atributo ausente no contexto não causa falso positivo.")

# Caso 3: Usuário válido no rollout
# user_123 com flag nova_ui tem hash 18 (18 < 50), logo True
assert engine.is_enabled("nova_ui", {"id": "user_123", "tier": "premium"}) == True
print("Sucesso: Usuário válido habilitado.")