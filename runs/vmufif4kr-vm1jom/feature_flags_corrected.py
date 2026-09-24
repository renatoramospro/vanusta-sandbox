import copy
import hashlib
import threading
import time
from typing import Any, Dict, List, Optional


class FeatureFlagContext:
    def __init__(self, user_id: str, attributes: Optional[Dict[str, Any]] = None):
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("user_id deve ser uma string não vazia")
        self.user_id = user_id
        self.attributes = attributes or {}


class FeatureFlagManager:
    def __init__(self):
        self._flags: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._evaluation_errors = 0
        self._total_evaluations = 0

    def set_flag(self, key: str, config: Dict[str, Any]):
        with self._lock:
            # Cópia defensiva para evitar mutação externa por referência
            self._flags[key] = copy.deepcopy(config)

    def get_error_rate(self) -> float:
        with self._lock:
            if self._total_evaluations == 0:
                return 0.0
            return (self._evaluation_errors / self._total_evaluations) * 100.0

    def evaluate(self, key: str, context: Optional[FeatureFlagContext], default: bool = False) -> bool:
        with self._lock:
            self._total_evaluations += 1

        try:
            with self._lock:
                if key not in self._flags:
                    return default
                # Cópia defensiva para thread-safety de leitura
                flag = copy.deepcopy(self._flags[key])

            # 1. Kill Switch Global (Se desativado, retorna o default ou False imediatamente)
            if not flag.get("enabled", True):
                return flag.get("default_value", default)

            if not context or not isinstance(context, FeatureFlagContext):
                raise ValueError("Contexto inválido ou ausente para avaliação segmentada")

            # 2. Override explícito por usuário (Whitelist / Blacklist)
            overrides = flag.get("user_overrides", {})
            if context.user_id in overrides:
                return overrides[context.user_id]

            # 3. Regras de Segmentação por Atributos
            for rule in flag.get("segment_rules", []):
                match = True
                for attr, expected_val in rule.get("conditions", {}).items():
                    actual_val = context.attributes.get(attr)
                    if actual_val != expected_val:
                        match = False
                        break
                if match:
                    return rule.get("value", True)

            # 4. Rollout Percentual (Hash Determinístico estável por versão/chave)
            rollout_percentage = flag.get("rollout_percentage", 0)
            if rollout_percentage > 0:
                version = flag.get("version", 1)
                hash_input = f"{key}:{version}:{context.user_id}".encode("utf-8")
                hash_val = int(hashlib.sha256(hash_input).hexdigest(), 16)
                bucket = hash_val % 100
                return bucket < rollout_percentage

            return flag.get("default_value", default)

        except Exception as e:
            with self._lock:
                self._evaluation_errors += 1
            # Fallback seguro em caso de erro de contexto ou processamento
            return default


def test_feature_flags_suite():
    manager = FeatureFlagManager()

    # Configuração de teste
    manager.set_flag("beta-feature", {
        "enabled": True,
        "version": 1,
        "default_value": False,
        "user_overrides": {"vip_user": True, "blocked_user": False},
        "segment_rules": [
            {"conditions": {"country": "BR", "plan": "enterprise"}, "value": True}
        ],
        "rollout_percentage": 30
    })

    # Teste 1: Flag inexistente retorna default
    assert manager.evaluate("non-existent", None, default=True) is True
    assert manager.evaluate("non-existent", None, default=False) is False

    # Teste 2: Kill switch global (enabled: false)
    manager.set_flag("beta-feature", {
        "enabled": False,
        "default_value": False
    })
    ctx = FeatureFlagContext("vip_user")
    assert manager.evaluate("beta-feature", ctx) is False, "Kill switch global deve desativar mesmo com override"

    # Restaurar flag ativada
    manager.set_flag("beta-feature", {
        "enabled": True,
        "version": 1,
        "default_value": False,
        "user_overrides": {"vip_user": True, "blocked_user": False},
        "segment_rules": [
            {"conditions": {"country": "BR", "plan": "enterprise"}, "value": True}
        ],
        "rollout_percentage": 30
    })

    # Teste 3: Overrides explícitos
    assert manager.evaluate("beta-feature", FeatureFlagContext("vip_user")) is True
    assert manager.evaluate("beta-feature", FeatureFlagContext("blocked_user")) is False

    # Teste 4: Segmentação por atributos
    ctx_segment = FeatureFlagContext("user_ comum", {"country": "BR", "plan": "enterprise"})
    assert manager.evaluate("beta-feature", ctx_segment) is True

    # Teste 5: Fallback e tratamento de erro com taxa de erro < 0.1%
    # Vamos disparar 10.000 avaliações, algumas com contexto inválido intencional para medir resiliência
    start_time = time.time()
    for i in range(10000):
        try:
            if i % 100 == 0:
                # Contexto deliberadamente inválido para testar captura de exceção
                manager.evaluate("beta-feature", None)
            else:
                manager.evaluate("beta-feature", FeatureFlagContext(f"user_{i}"))
        except Exception:
            pass

    error_rate = manager.get_error_rate()
    print(f"Total de avaliações: {manager._total_evaluations}")
    print(f"Erros capturados e tratados com fallback: {manager._evaluation_errors}")
    print(f"Taxa de erro medida: {error_rate:.4f}%")

    assert error_rate < 0.1, f"Taxa de erro {error_rate}% acima do limite de 0.1%"
    print("Sucesso: Todos os testes rigorosos passaram e a taxa de erro está abaixo de 0,1%!")


if __name__ == "__main__":
    test_feature_flags_suite()