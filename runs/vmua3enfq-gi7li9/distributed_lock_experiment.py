import time
import threading

class DistributedStore:
    """Simula um servidor central (ex: Redis ou Etcd)"""
    def __init__(self):
        self.data = {}
        self.locks = {}  # key -> (token, expiry)
        self.last_fencing_token = {}  # key -> last_successful_token
        self.global_token_counter = 0
        self.lock = threading.Lock()

    def acquire_lock(self, key, ttl_seconds):
        with self.lock:
            now = time.time()
            # Verifica se o lock existe e não expirou
            if key in self.locks:
                token, expiry = self.locks[key]
                if now < expiry:
                    return None  # Lock ainda ocupado

            # Concede novo lock
            self.global_token_counter += 1
            new_token = self.global_token_counter
            self.locks[key] = (new_token, now + ttl_seconds)
            return new_token

    def write(self, key, value, token, use_fencing=True):
        with self.lock:
            if use_fencing:
                last_token = self.last_fencing_token.get(key, 0)
                if token <= last_token:
                    raise Exception(f"FENCING REJECTED: Token {token} is stale. Last successful token was {last_token}")
                self.last_fencing_token[key] = token
            
            self.data[key] = value
            return True

def run_scenario(use_fencing):
    store = DistributedStore()
    key = "critical_resource"
    store.data[key] = 0
    
    print(f"\n--- Iniciando Cenário: {'COM Fencing' if use_fencing else 'SEM Fencing (Vulnerável)'} ---")

    # 1. Nó A adquire o lock
    token_a = store.acquire_lock(key, ttl_seconds=1)
    print(f"[Nó A] Lock adquirido com Token: {token_a}")

    # 2. Simulação de "Pausa de Processo" (Nó A congela por 2 segundos)
    # O TTL é de 1 segundo, então o lock vai expirar enquanto o Nó A dorme.
    print("[Nó A] Entrando em pausa longa (simulando GC pause/rede)...")
    time.sleep(2)

    # 3. Enquanto o Nó A está "congelado", o Nó B entra e faz tudo
    token_b = store.acquire_lock(key, ttl_seconds=1)
    if token_b:
        print(f"[Nó B] Lock adquirido com Token: {token_b}")
        store.write(key, 100, token_b, use_fencing=use_fencing)
        print(f"[Nó B] Escrita realizada: valor={store.data[key]}")
    else:
        print("[Nó B] Falha ao adquirir lock (esperado se o lock não tivesse expirado)")

    # 4. Nó A "acorda" e tenta completar sua operação
    print(f"[Nó A] Acordou! Tentando escrever valor=50 com Token: {token_a}")
    try:
        store.write(key, 50, token_a, use_fencing=use_fencing)
        print(f"[Nó A] Escrita realizada com sucesso: valor={store.data[key]}")
    except Exception as e:
        print(f"[Nó A] Erro de segurança: {e}")

    # Verificação Final
    final_val = store.data[key]
    if use_fencing:
        if final_val == 100:
            print(">>> RESULTADO: SUCESSO. Consistência mantida (Valor final é 100).")
        else:
            print(f">>> RESULTADO: FALHA. Corrupção detectada! Valor final: {final_val}")
    else:
        if final_val == 50:
            print(">>> RESULTADO: FALHA. Corrupção detectada! O processo zumbi sobrescreveu o dado (Valor final: 50).")
        else:
            print(f">>> RESULTADO: SUCESSO. Valor final: {final_val}")

if __name__ == "__main__":
    # Teste 1: O erro comum (sem proteção de fencing)
    run_scenario(use_fencing=False)
    
    # Teste 2: A implementação correta (com proteção de fencing)
    run_scenario(use_fencing=True)