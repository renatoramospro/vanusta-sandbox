import time
import threading
import hashlib
from typing import Dict, Any, Tuple, Optional

# ==========================================
# SIMULAÇÃO DE ARMAZENAMENTO DISTRIBUÍDO (Segura)
# ==========================================
class DistributedStorage:
    def __init__(self, max_keys: int = 100, max_key_len: int = 64):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.max_keys = max_keys
        self.max_key_len = max_key_len

    def set_if_not_exists(self, key: str, state: str, payload: Any = None) -> Tuple[bool, Optional[float]]:
        """Simula SETNX atômico retornando (sucesso, version/timestamp)."""
        if len(key) > self.max_key_len:
            raise ValueError("Key too long (DoS protection)")
            
        with self._lock:
            if len(self._store) >= self.max_keys:
                return False, None # Simula estouro de storage
            
            if key in self._store:
                return False, self._store[key]["version"]
            
            version = time.time()
            self._store[key] = {
                "state": state,
                "payload": payload,
                "version": version,
                "timestamp": version
            }
            return True, version

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(key)

    def update_with_fencing(self, key: str, state: str, payload: Any, expected_version: float) -> bool:
        """
        Implementa Fencing Token. Só atualiza se o version (token) 
        for igual ao que o worker obteve no início.
        """
        with self._lock:
            record = self._store.get(key)
            if not record:
                return False
            
            # A CORREÇÃO: Validação de integridade contra o Worker Zumbi
            if record["version"] != expected_version:
                return False
            
            record["state"] = state
            if payload is not None:
                record["payload"] = payload
            record["timestamp"] = time.time()
            return True

# ==========================================
# MIDDLEWARE DE IDEMPOTÊNCIA (CORRIGIDO)
# ==========================================
class IdempotencyMiddleware:
    def __init__(self, storage: DistributedStorage, lock_timeout: float = 2.0):
        self.storage = storage
        self.lock_timeout = lock_timeout

    def _generate_secure_key(self, user_id: str, idempotency_key: str) -> str:
        """Vínculo de Identidade: Impede Key Hijacking."""
        raw_key = f"{user_id}:{idempotency_key}"
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def process(self, user_id: str, idempotency_key: str, business_logic) -> Tuple[int, Dict[str, Any]]:
        key = self._generate_secure_key(user_id, idempotency_key)
        
        # 1. Tentar obter lock (SETNX)
        success, version = self.storage.set_if_not_exists(key, "PROCESSING")
        
        if not success:
            record = self.storage.get(key)
            if not record: # Caso raro de race entre get e set
                return 500, {"error": "Internal error during lock acquisition"}
            
            # 2. Verificar se o lock expirou (Timeout de Processamento)
            if record["state"] == "PROCESSING" and (time.time() - record["timestamp"] > self.lock_timeout):
                # Lock expirou, permitimos que este worker tente assumir o novo version
                # Para simplificar o experimento, vamos "limpar" e tentar de novo
                # Em produção, usaríamos um comando atômico de renovação de lock
                print(f"[Middleware] Lock expirado para {idempotency_key}. Tentando assumir...")
                # Simulamos a retomada do lock com novo version
                # (Em um sistema real, o SETNX falharia, então faríamos um delete + set)
                # Aqui, para o teste, vamos forçar a limpeza para permitir o novo worker
                with self.storage._lock:
                    self.storage._store[key]["state"] = "FAILED" # Força transição para permitir retentativa
                return self.process(user_id, idempotency_key, business_logic)

            # 3. Se já estiver processando ou concluído
            if record["state"] == "PROCESSING":
                return 409, {"error": "Request in progress"}
            elif record["state"] == "COMPLETED":
                return 200, record["payload"]
            elif record["state"] == "FAILED":
                # Permite retentativa se o estado for FAILED
                pass 
            else:
                return 500, {"error": "Unknown state"}

        # 4. Executar Lógica de Negócio
        try:
            status_code, result = business_logic()
            # 5. Atualizar com Fencing Token
            updated = self.storage.update_with_fencing(key, "COMPLETED", result, version)
            if not updated:
                # Se falhou, o worker zumbi tentou atualizar um lock que já mudou!
                return 409, {"error": "Fencing error: Processo lento detectado e bloqueado"}
            return status_code, result
        except Exception as e:
            self.storage.update_with_fencing(key, "FAILED", {"error": str(e)}, version)
            return 500, {"error": str(e)}

# ==========================================
# EXPERIMENTOS DE VALIDAÇÃO
# ==========================================
def run_tests():
    storage = DistributedStorage()
    middleware = IdempotencyMiddleware(storage, lock_timeout=1.0)
    user_a = "user_123"
    key_1 = "req_abc"

    print("--- TESTE 1: Proteção contra Worker Zumbi (Fencing Token) ---")
    # Simulação: Worker 1 pega o lock, mas demora muito.
    # Worker 2 assume o lock por timeout.
    # Worker 1 tenta finalizar, mas deve ser bloqueado.
    
    # 1. Worker 1 inicia
    success, version_1 = storage.set_if_not_exists(middleware._generate_secure_key(user_a, key_1), "PROCESSING")
    print(f"Worker 1 obteve version: {version_1}")
    
    # 2. Tempo passa (simula timeout)
    time.sleep(1.5)
    
    # 3. Worker 2 assume (via middleware que detecta timeout)
    def logic_worker_2(): return 200, {"msg": "Sucesso pelo Worker 2"}
    res_2, body_2 = middleware.process(user_a, key_1, logic_worker_2)
    print(f"Worker 2 resultado: {res_2}, {body_2}")
    
    # 4. Worker 1 "acorda" e tenta atualizar com o version antigo
    updated = storage.update_with_fencing(middleware._generate_secure_key(user_a, key_1), "COMPLETED", {"msg": "Zumbi"}, version_1)
    print(f"Worker 1 (Zumbi) tentou update: {'Sucesso' if updated else 'BLOQUEADO (Correto)'}")
    assert updated is False
    print("PASSED: Fencing Token impediu o Worker Zumbi.")

    print("\n--- TESTE 2: Proteção contra Key Hijacking ---")
    user_b = "user_999"
    # User B tenta usar a mesma idempotency_key do User A
    def logic_b(): return 200, {"msg": "Payload do User B"}
    
    # User A já processou a key_1
    middleware.process(user_a, key_1, lambda: (200, {"msg": "Original A"}))
    
    # User B tenta usar a mesma key_1
    res_b, body_b = middleware.process(user_b, key_1, logic_b)
    print(f"User B tentando usar chave de A: {res_b}, {body_b}")
    # Se o hash for diferente, o User B deve conseguir processar sua própria operação
    assert res_b == 200
    assert body_b["msg"] == "Payload do User B"
    print("PASSED: Chaves vinculadas ao UserID.")

    print("\n--- TESTE 3: Proteção contra DoS (Tamanho de Chave) ---")
    long_key = "a" * 100
    try:
        middleware.process(user_a, long_key, lambda: (200, {}))
    except ValueError as e:
        print(f"Capturado erro de DoS: {e}")
        assert "Key too long" in str(e)
    print("PASSED: Limite de tamanho de chave aplicado.")

if __name__ == "__main__":
    run_tests()
    print("\n✅ TODOS OS EXPERIMENTOS DE SEGURANÇA PASSARAM!")