import time
import threading

class DistributedCache:
    def __init__(self, ttl_seconds=2):
        self.cache = {}  # {key: {"value": v, "version": v, "expiry": t}}
        self.db = {"user:1": {"value": "V1", "version": 1}}
        self.ttl = ttl_seconds
        self.lock = threading.Lock()

    def get(self, key):
        # 1. Verifica cache e expiração (TTL)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry["expiry"]:
                return entry["value"]
            else:
                del self.cache[key] # Expurgado
        
        # 2. Busca no DB (Simulação)
        data = self.db.get(key)
        if data:
            self.cache[key] = {
                "value": data["value"],
                "version": data["version"],
                "expiry": time.time() + self.ttl
            }
            return data["value"]
        return None

    def handle_invalidation_event(self, key, new_value, new_version):
        """Simula recebimento de evento via Pub/Sub com versionamento."""
        with self.lock:
            # Proteção contra eventos fora de ordem (Regressão de estado)
            if key in self.cache and self.cache[key]["version"] >= new_version:
                print(f"[Ignorado] Evento obsoleto para {key}")
                return
            
            self.cache[key] = {
                "value": new_value,
                "version": new_version,
                "expiry": time.time() + self.ttl
            }
            print(f"[Atualizado] Chave {key} para versão {new_version}")

# --- Testes de Validação ---
cache = DistributedCache()

# 1. Teste de TTL
print(f"Leitura: {cache.get('user:1')}")
time.sleep(2.1)
print(f"Leitura após TTL expirar: {cache.get('user:1')}")

# 2. Teste de Versionamento (Evitar regressão)
cache.handle_invalidation_event('user:1', 'V2', 2)
cache.handle_invalidation_event('user:1', 'V1_Atrasado', 1) # Deve ser ignorado
print(f"Valor final após tentativa de regressão: {cache.get('user:1')}")