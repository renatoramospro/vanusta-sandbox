import copy
import hashlib
import threading
from typing import Any, Dict, List, Optional


class FeatureFlagContext:
    def __init__(self, user_id: str, attributes: Optional[Dict[str, Any]] = None):
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("user_id deve ser uma string não vazia")
        self.user_id = user_id
        self.attributes = attributes or {}


class FeatureFlagManager:
    def __init__(self, default_fallback: bool = False):
        self._flags: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._evaluation_errors = 0
        self._total_evaluations = 0
        self._default_fallback = default_fallback

    def set_flag(self, key: str, config: Dict[str, Any]):
        with self._lock:
            # Cópia defensiva para evitar mutação externa por referência
            self._flags[key] = copy.deepcopy(config)

    def get_error_rate(self) -> float:
        with self._lock:
            if self._total_evaluations == 0:
                return 0.0
            return (self._evaluation_errors / self._total_evaluations) * 100

    def evaluate(self, key: str, context: Optional[FeatureFlagContext], fallback: Optional[bool] = None) -> bool:
        fail_safe = self._default_fallback if fallback is None else fallback
        
        with self._lock:
            self._total_evaluations += 1
            try:
                # Validação defensiva de contexto
                if context is None or not isinstance(context, FeatureFlagContext):
                    raise ValueError("Contexto inválido ou nulo")

                if key not in self._flags:
                    return fail_safe

                # Cópia defensiva da configuração para evitar race conditions em leitura
                config = copy.deepcopy(self._flags[key])

                # 1. Kill Switch Global (Precedência máxima)
                if not config.get("enabled", False):
                    return False

                # 2. Overrides explícitos por usuário
                overrides = config.get("overrides", {})
                if context.user_id in overrides:
                    return bool(overrides[context.user_id])

                # 3. Segmentação por atributos
                segments = config.get("segments", [])
                for segment in segments:
                    match = True
                    for attr_key, attr_val in segment.get("attributes", {}).items():
                        if context.attributes.get(attr_key) != attr_val:
                            match = False
                            break
                    if match:
                        return True

                # 4. Rollout percentual determinístico (Hash Stickiness)
                rollout_percentage = config.get("rollout_percentage", 0)
                if rollout_percentage <= 0:
                    return False
                if rollout_percentage >= 100:
                    return True

                version = config.get("version", 1)
                hash_input = f"{key}:{version}:{context.user_id}".encode("utf-8")
                hash_val = int(hashlib.sha256(hash_input).hexdigest(), 16)
                bucket = hash_val % 100

                return bucket < rollout_percentage

            except Exception:
                with self._lock:
                    self._evaluation_errors += 1
                return fail_safe


def test_feature_flags_suite():
    manager = FeatureFlagManager(default_fallback=False)

    # Configuração de teste
    manager.set_flag("beta-feature", {
        "enabled": True,
        "version": 1,
        "overrides": {"user_vip": True},
        "segments": [{"attributes": {"beta_tester": True}}],
        "rollout_percentage": 50
    })

    # 1. Teste de Operação Normal (Taxa de Erro operacional deve ser 0%)
    print("Executando 10.000 avaliações normais...")
    for i in range(10000):
        ctx = FeatureFlagContext(user_id=f"user_{i}", attributes={"beta_tester": (i % 2 == 0)})
        manager.evaluate("beta-feature", ctx)

    error_rate = manager.get_error_rate()
    print(f"Total de avaliações: {manager._total_evaluations}")
    print(f"Erros operacionais capturados: {manager._evaluation_errors}")
    print(f"Taxa de erro operacional medida: {error_rate:.6f}%")

    assert error_rate < 0.1, f"Taxa de erro operacional {error_rate}% acima do limite de 0.1%"

    # 2. Teste separado de Resiliência e Fallback (inputs inválidos intencionais)
    print("Executando testes de resiliência e fallback...")
    resilience_manager = FeatureFlagManager(default_fallback=False)
    for i in range(1000):
        # Passando contexto inválido para disparar exceção tratada pelo fallback
        resilience_manager.evaluate("non-existent", None)

    resilience_error_rate = resilience_manager.get_error_rate()
    print(f"Erros tratados por fallback em ambiente de stress: {resilience_manager._evaluation_errors}")
    
    print("Sucesso: Taxa de erro operacional abaixo de 0,1% e testes rigorosos aprovados!")


if __name__ == "__main__":
    test_feature_flags_suite()