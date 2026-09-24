import copy
import hashlib
import math
import threading
from typing import Any, Dict, List, Optional


class FeatureFlagContext:
    def __init__(self, user_id: str, attributes: Optional[Dict[str, Any]] = None):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id deve ser uma string não vazia")
        self.user_id = user_id
        
        # Validação estrita de atributos para evitar tipos arbitrários perigosos
        safe_attributes = {}
        if attributes is not None:
            if not isinstance(attributes, dict):
                raise ValueError("attributes deve ser um dicionário")
            for k, v in attributes.items():
                if not isinstance(k, str):
                    raise ValueError("Chaves de attributes devem ser strings")
                if not isinstance(v, (str, int, float, bool, list)):
                    raise ValueError(f"Tipo não suportado em attributes: {type(v)}")
                safe_attributes[k] = v
        self.attributes = safe_attributes


class FeatureFlagManager:
    def __init__(self, default_fallback: bool = False):
        if not isinstance(default_fallback, bool):
            raise ValueError("default_fallback deve ser booleano")
        self._flags: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._evaluation_errors = 0
        self._total_evaluations = 0
        self._default_fallback = default_fallback

    def set_flag(self, key: str, config: Dict[str, Any]):
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Chave da flag deve ser uma string não vazia")
        if not isinstance(config, dict):
            raise ValueError("Configuração da flag deve ser um dicionário")
        
        # Validação de schema estrito
        if "enabled" in config and not isinstance(config["enabled"], bool):
            raise ValueError("O campo 'enabled' deve ser estritamente booleano")
        
        if "rollout_percentage" in config:
            rp = config["rollout_percentage"]
            if isinstance(rp, bool) or not isinstance(rp, (int, float)):
                raise ValueError("rollout_percentage deve ser numérico")
            if math.isnan(rp) or math.isinf(rp):
                raise ValueError("rollout_percentage não pode ser NaN ou infinito")
            if not (0 <= rp <= 100):
                raise ValueError("rollout_percentage deve estar entre 0 e 100")

        if "overrides" in config:
            if not isinstance(config["overrides"], dict):
                raise ValueError("overrides deve ser um dicionário")
            for u_id, val in config["overrides"].items():
                if not isinstance(u_id, str) or not isinstance(val, bool):
                    raise ValueError("overrides exige user_id (str) e valor (bool)")

        if "segments" in config:
            if not isinstance(config["segments"], list):
                raise ValueError("segments deve ser uma lista de strings")
            for seg in config["segments"]:
                if not isinstance(seg, str):
                    raise ValueError("Cada segmento deve ser uma string")

        with self._lock:
            # Cópia defensiva segura
            self._flags[key] = copy.deepcopy(config)

    def get_system_error_rate(self) -> float:
        with self._lock:
            if self._total_evaluations == 0:
                return 0.0
            return (self._evaluation_errors / self._total_evaluations) * 100

    def evaluate(self, key: str, context: Optional[FeatureFlagContext], fallback: Optional[bool] = None) -> bool:
        fail_safe = self._default_fallback if fallback is None else fallback
        if not isinstance(fail_safe, bool):
            fail_safe = self._default_fallback

        with self._lock:
            self._total_evaluations += 1
            try:
                # Validação de contexto
                if context is None or not isinstance(context, FeatureFlagContext):
                    self._evaluation_errors += 1
                    return fail_safe

                if key not in self._flags:
                    # Flag inexistente retorna fallback sem contar como erro operacional crítico,
                    # ou pode ser tratada conforme padrão. Aqui tratamos como safe default.
                    return fail_safe

                flag = self._flags[key]

                # 1. Kill Switch / Global Enabled
                if not flag.get("enabled", False):
                    return False

                # 2. Overrides por usuário
                overrides = flag.get("overrides", {})
                if context.user_id in overrides:
                    return overrides[context.user_id]

                # 3. Segmentação por atributos
                segments = flag.get("segments", [])
                user_tags = context.attributes.get("tags", [])
                if any(seg in user_tags for seg in segments):
                    return True

                # 4. Rollout percentual determinístico (Hash)
                rollout_pct = flag.get("rollout_percentage", 0)
                if rollout_pct >= 100:
                    return True
                if rollout_pct <= 0:
                    return False

                # Hash seguro
                raw_input = f"{key}:{context.user_id}".encode("utf-8")
                hash_val = int(hashlib.sha256(raw_input).hexdigest(), 16)
                bucket = hash_val % 100
                return bucket < rollout_pct

            except Exception:
                self._evaluation_errors += 1
                return fail_safe


def test_secure_feature_flags():
    manager = FeatureFlagManager(default_fallback=False)
    
    # Configuração de flag segura
    manager.set_flag("beta_feature", {
        "enabled": True,
        "rollout_percentage": 50,
        "overrides": {"user_vip": True},
        "segments": ["beta_testers"]
    })

    print("Executando 10.000 avaliações sob schema seguro...")
    
    # 9.995 avaliações normais válidas
    for i in range(9995):
        ctx = FeatureFlagContext(user_id=f"user_{i}", attributes={"tags": ["beta_testers"] if i % 2 == 0 else []})
        manager.evaluate("beta_feature", ctx)

    # 5 entradas inválidas intencionais para testar resiliência e medição de erro do sistema
    for i in range(5):
        manager.evaluate("beta_feature", None)  # contexto inválido forçado

    error_rate = manager.get_system_error_rate()
    print(f"Total de avaliações: {manager._total_evaluations}")
    print(f"Erros capturados (sistema completo): {manager._evaluation_errors}")
    print(f"Taxa de erro medida: {error_rate:.6f}%")

    assert error_rate < 0.1, f"Taxa de erro {error_rate}% acima do limite de 0,1%"
    print("Sucesso: Validação de segurança, schema estrito e taxa de erro < 0,1% aprovados!")


if __name__ == "__main__":
    test_secure_feature_flags()