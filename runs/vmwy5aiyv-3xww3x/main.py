import time
import threading
import json
from typing import Dict, Any, Callable

# =====================================================================
# MÓDULO DE CONFIGURAÇÃO DINÂMICA
# =====================================================================

class ConfigurationError(Exception):
    """Exceção lançada quando ocorre falha na validação ou aplicação da configuração."""
    pass

class DynamicConfigManager:
    """
    Gerenciador de configuração dinâmica com suporte a troca atômica,
    validação de schema e rollback automático.
    """
    def __init__(self, initial_config: Dict[str, Any], schema: Dict[str, type]):
        self._config = initial_config
        self._schema = schema
        self._lock = threading.Lock()
        self._listeners: list[Callable[[Dict[str, Any]], None]] = []

    def register_listener(self, callback: Callable[[Dict[str, Any]], None]):
        """Registra um observador para ser notificado em mudanças de configuração."""
        with self._lock:
            self._listeners.append(callback)

    def get_config(self) -> Dict[str, Any]:
        """Retorna uma cópia da configuração atual (leitura thread-safe)."""
        with self._lock:
            return self._config.copy()

    def _validate(self, new_config: Dict[str, Any]) -> None:
        """Valida tipos e chaves obrigatórias conforme o schema."""
        for key, expected_type in self._schema.items():
            if key not in new_config:
                raise ConfigurationError(f"Chave obrigatória ausente: '{key}'")
            if not isinstance(new_config[key], expected_type):
                raise ConfigurationError(
                    f"Tipo inválido para '{key}'. Esperado: {expected_type.__name__}, "
                    f"obtido: {type(new_config[key]).__name__}"
                )

    def update_config(self, new_config: Dict[str, Any]) -> float:
        """
        Aplica nova configuração de forma atômica com medição de performance.
        Retorna o tempo de aplicação em milissegundos.
        """
        start_time = time.perf_counter()
        
        # 1. Validação fora do lock pesado para evitar gargalos de I/O/CPU
        try:
            self._validate(new_config)
        except Exception as e:
            raise ConfigurationError(f"Falha na validação da configuração: {e}")

        with self._lock:
            old_config = self._config
            # 2. Troca atômica de referência (Imutabilidade de estado)
            self._config = new_config.copy()
            
            try:
                # 3. Notificação dos subsistemas dependentes
                for listener in self._listeners:
                    listener(self._config)
            except Exception as e:
                # 4. ROLLBACK AUTOMÁTICO em caso de falha nos listeners
                self._config = old_config
                raise ConfigurationError(f"Erro ao aplicar configuração nos subsistemas. Rollback executado: {e}")

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000.0
        return elapsed_ms

# =====================================================================
# EXPERIMENTO E TESTES REPRODUTÍVEIS
# =====================================================================

def run_experiment():
    print("=== INICIANDO EXPERIMENTO DE CONFIGURAÇÃO DINÂMICA ===")
    
    # Schema esperado
    schema = {
        "timeout": int,
        "max_connections": int,
        "feature_flag": bool,
        "environment": str
    }
    
    initial_data = {
        "timeout": 30,
        "max_connections": 100,
        "feature_flag": False,
        "environment": "staging"
    }
    
    manager = DynamicConfigManager(initial_data, schema)
    
    # Subsistema simulado que reage à configuração
    applied_updates = []
    def mock_subsystem_listener(cfg):
        applied_updates.append(cfg)

    manager.register_listener(mock_subsystem_listener)

    # 5 Mudanças de configuração distintas
    changes = [
        {"timeout": 15, "max_connections": 200, "feature_flag": True, "environment": "production"},
        {"timeout": 10, "max_connections": 300, "feature_flag": True, "environment": "production"},
        {"timeout": 5,  "max_connections": 500, "feature_flag": False, "environment": "production"},
        {"timeout": 60, "max_connections": 50,  "feature_flag": False, "environment": "staging"},
        {"timeout": 20, "max_connections": 150, "feature_flag": True, "environment": "staging"},
    ]

    print("\n[Teste 1] Processando 5 mudanças de configuração distintas:")
    for i, new_data in enumerate(changes, 1):
        try:
            latency_ms = manager.update_config(new_data)
            print(f"  -> Mudança {i}: Sucesso em {latency_ms:.4f} ms (< 50ms)")
            assert latency_ms < 50.0, f"Latência excedeu 50ms: {latency_ms}ms"
        except ConfigurationError as e:
            print(f"  -> Mudança {i}: Falhou inesperadamente: {e}")
            raise

    # Verificação de consistência de estado final
    final_config = manager.get_config()
    assert final_config == changes[-1], "O estado final não corresponde à última configuração aplicada."
    print("\n[Sucesso] Todas as 5 mudanças aplicadas com sucesso e dentro da latência limite!")

    # [CONTRAEXEMPLO / ATAQUE AO EQUÍVOCO COMUM]
    # Equívoco comum: Mutação in-place sem validação nem rollback (estado inconsistente parcial).
    print("\n[Teste 2] Testando comportamento de Rollback sob falha:")
    
    def faulty_listener(cfg):
        if cfg["timeout"] == 999:
            raise RuntimeError("Falha catastrófica no subsistema!")

    manager.register_listener(faulty_listener)
    
    invalid_or_failing_config = {
        "timeout": 999, # Disparará a falha no listener
        "max_connections": 1000,
        "feature_flag": True,
        "environment": "production"
    }

    state_before_failure = manager.get_config()
    
    try:
        manager.update_config(invalid_or_failing_config)
    except ConfigurationError as err:
        print(f"  -> Capturado erro esperado: {err}")

    state_after_failure = manager.get_config()
    
    # Valida se o rollback foi efetivo
    assert state_before_failure == state_after_failure, "Falha: O estado do sistema foi corrompido após erro (sem rollback)!"
    print("  -> Rollback verificado com sucesso: o sistema manteve o estado anterior íntegro.")

if __name__ == "__main__":
    run_experiment()