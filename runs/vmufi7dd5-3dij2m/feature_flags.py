import hashlib
import threading
from typing import Any, Dict, List, Optional


class FeatureFlagContext:
    def __init__(self, user_id: str, attributes: Optional[Dict[str, Any]] = None):
        self.user_id = user_id
        self.attributes = attributes or {}


class FeatureFlagManager:
    def __init__(self):
        self._flags: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def set_flag(self, key: str, config: Dict[str, Any]):
        with self._lock:
            self._flags[key] = config

    def evaluate(self, key: str, context: Optional[FeatureFlagContext], default: bool = False) -> bool:
        with self._lock:
            if key not in self._flags:
                return default
            flag = self._flags[key]

        # 1. Estado Global desativado (curto-circuito)
        if not flag.get("enabled", False):
            return False

        if not context:
            return flag.get("default_value", default)

        # 2. Override explícito por usuário (whitelist / blacklist)
        overrides = flag.get("user_overrides", {})
        if context.user_id in overrides:
            return overrides[context.user_id]

        # 3. Regras de Segmentação (Atributos)
        for rule in flag.get("segment_rules", []):
            match = True
            for attr, expected_val in rule.get("conditions", {}).items():
                actual_val = context.attributes.get(attr)
                if actual_val != expected_val:
                    match = False
                    break
            if match:
                return rule.get("value", True)

        # 4. Rollout Percentual (Hash Determinístico)
        rollout_percentage = flag.get("rollout_percentage", 0)
        if rollout_percentage > 0:
            if rollout_percentage >= 100:
                return True
            # Hash determinístico combinando chave da flag e ID do usuário
            hash_input = f"{key}:{context.user_id}".encode("utf-8")
            hash_int = int(hashlib.sha256(hash_input).hexdigest(), 16)
            bucket = hash_int % 100
            return bucket < rollout_percentage

        # 5. Padrão Global
        return flag.get("default_value", default)


# --- Testes Unitários Demonstrando o Comportamento ---

def test_feature_flag_evaluation():
    manager = FeatureFlagManager()

    # Configuração de flag complexa
    manager.set_flag("nova-home", {
        "enabled": True,
        "default_value": False,
        "user_overrides": {
            "usuario_vip": True,
            "usuario_banido": False
        },
        "segment_rules": [
            {
                "conditions": {"country": "BR", "plan": "enterprise"},
                "value": True
            }
        ],
        "rollout_percentage": 30
    })

    # Teste 1: Flag inexistente retorna default
    assert manager.evaluate("nao-existe", FeatureFlagContext("u1")) is False

    # Teste 2: Override de usuário (VIP)
    ctx_vip = FeatureFlagContext("usuario_vip")
    assert manager.evaluate("nova-home", ctx_vip) is True

    # Teste 3: Override de usuário (Banido)
    ctx_banido = FeatureFlagContext("usuario_banido")
    assert manager.evaluate("nova-home", ctx_banido) is False

    # Teste 4: Regra de segmentação (BR + Enterprise)
    ctx_seg = FeatureFlagContext("u_normal", {"country": "BR", "plan": "enterprise"})
    assert manager.evaluate("nova-home", ctx_seg) is True

    # Teste 5: Rollout percentual determinístico e consistência
    # O mesmo usuário deve obter sempre o mesmo resultado para a mesma flag
    ctx_rollout = FeatureFlagContext("usuario_comum_123")
    res1 = manager.evaluate("nova-home", ctx_rollout)
    res2 = manager.evaluate("nova-home", ctx_rollout)
    assert res1 == res2, "O rollout percentual deve ser determinístico para o mesmo usuário"

    print("Todos os testes unitários passaram com sucesso!")

if __name__ == "__main__":
    test_feature_flag_evaluation()