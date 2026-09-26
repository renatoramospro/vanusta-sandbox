import time
import uuid
import threading
from typing import Optional, Dict

class DistributedLockManager:
    """
    Simula um Gerenciador de Travas Distribuído baseado em Recursos Compartilhados com TTL.
    """
    def __init__(self):
        self._storage: Dict[str, Dict] = {} # resource_id -> {owner_id, expires_at}
        self._lock = threading.Lock() # Protege o armazenamento simulado

    def acquire(self, resource_id: str, owner_id: str, ttl_seconds: float) -> bool:
        """
        Tenta adquirir a trava para um recurso.
        Garante exclusão mútua e respeita o TTL de travas expiradas.
        """
        with self._lock:
            now = time.time()
            current_lock = self._storage.get(resource_id)

            # Se a trava existe mas já expirou, nós a removemos (TTL vencido)
            if current_lock and current_lock["expires_at"] <= now:
                print(f"[LockManager] ⏰ Trava para '{resource_id}' expirou (TTL vencido). Liberando automaticamente.")
                self._storage.pop(resource_id, None)
                current_lock = None

            # Se ainda está ocupada por outro dono
            if current_lock:
                return False

            # Adquire a trava
            self._storage[resource_id] = {
                "owner_id": owner_id,
                "expires_at": now + ttl_seconds
            }
            return True

    def release(self, resource_id: str, owner_id: str) -> bool:
        """
        Libera a trava apenas se o owner_id for o proprietário atual.
        Isso evita liberação cega (equívoco comum).
        """
        with self._lock:
            current_lock = self._storage.get(resource_id)
            if not current_lock:
                return True # Já está livre
            
            if current_lock["owner_id"] != owner_id:
                print(f"[LockManager] ⚠️ ALERTA: '{owner_id}' tentou liberar trava de '{current_lock['owner_id']}'!")
                return False

            self._storage.pop(resource_id, None)
            return True


# ==========================================
# TESTES E DEMONSTRAÇÕES EXECUTÁVEIS
# ==========================================

def test_exclusao_mutua():
    print("--- Teste 1: Exclusão Mútua Básica ---")
    manager = DistributedLockManager()
    res = "recurso_financeiro"
    
    proc_A = "Processo-A"
    proc_B = "Processo-B"

    # Processo A adquire a trava
    assert manager.acquire(res, proc_A, ttl_seconds=5.0) == True
    print(f"{proc_A} adquiriu a trava com sucesso.")

    # Processo B tenta adquirir a mesma trava e deve falhar
    assert manager.acquire(res, proc_B, ttl_seconds=5.0) == False
    print(f"{proc_B} tentou adquirir a trava e foi bloqueado (Exclusão Mútua garantida).")

    # Processo A libera
    assert manager.release(res, proc_A) == True
    print(f"{proc_A} liberou a trava.")

    # Agora Processo B deve conseguir
    assert manager.acquire(res, proc_B, ttl_seconds=5.0) == True
    print(f"{proc_B} adquiriu a trava após a liberação do Processo A.")
    manager.release(res, proc_B)


def test_ttl_previne_deadlock():
    print("\n--- Teste 2: TTL Previne Deadlock (Falha do Processo) ---")
    manager = DistributedLockManager()
    res = "recurso_critico"

    proc_crashado = "Processo-Crashado"
    proc_sobrevivente = "Processo-Sobrevivente"

    # Processo crashado pega a trava com TTL curto (0.2 segundos)
    assert manager.acquire(res, proc_crashado, ttl_seconds=0.2) == True
    print(f"{proc_crashado} adquiriu a trava e simulou crash (TTL curto de 0.2s).")

    # Simula o tempo passando além do TTL
    time.sleep(0.3)

    # Processo sobrevivente tenta pegar a trava. Como expirou, DEVE conseguir (evitando deadlock)
    acquired = manager.acquire(res, proc_sobrevivente, ttl_seconds=5.0)
    assert acquired == True, "O TTL falhou em liberar a trava, causando deadlock!"
    print(f"⏰ TTL expirou com sucesso! {proc_sobrevivente} adquiriu a trava do processo inativo.")
    
    manager.release(res, proc_sobrevivente)


def test_contraexemplo_liberacao_cega():
    print("\n--- Teste 3: Contraexemplo (O perigo da Liberação Cega sem Validação) ---")
    manager = DistributedLockManager()
    res = "recurso_sensivel"

    # Processo A pega a trava por muito pouco tempo e expira
    manager.acquire(res, owner_id="Processo-A", ttl_seconds=0.1)
    time.sleep(0.2) # Trava expira e é tomada pelo Processo B
    
    manager.acquire(res, owner_id="Processo-B", ttl_seconds=5.0)
    print("Processo B assumiu a trava após expiração legítima.")

    # Se tivéssemos uma implementação ingênua que libera sem checar o dono (liberação cega):
    # Processo A acorda atrasado e tenta liberar o que não é mais dele
    released_by_wrong_owner = manager.release(res, owner_id="Processo-A")
    
    # Nossa implementação correta BLOQUEIA a liberação indevida:
    assert released_by_wrong_owner == False
    print("🛡️ Segurança validada: Processo A foi impedido de corromper a trava do Processo B!")
    
    manager.release(res, owner_id="Processo-B")


if __name__ == "__main__":
    test_exclusao_mutua()
    test_ttl_previne_deadlock()
    test_contraexemplo_liberacao_cega()
    print("\nTodos os testes executados com sucesso absoluto!")