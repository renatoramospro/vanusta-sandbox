import time
import threading
import random

class DistributedCache:
    def __init__(self):
        self.cache = {}
        self.db = {"user:1": "Versao_Original"}
        self.lock = threading.Lock()
        self.inflight = {}

    def get(self, key):
        # 1. Tenta ler do cache
        if key in self.cache:
            return self.cache[key]
        
        # 2. Proteção contra Cache Stampede (Single-Flight)
        with self.lock:
            if key in self.inflight:
                return "Aguardando_DB"
            self.inflight[key] = True
        
        # Simula latência de banco
        time.sleep(0.5) 
        val = self.db.get(key)
        self.cache[key] = val
        
        with self.lock:
            del self.inflight[key]
        return val

    def invalidate(self, key):
        if key in self.cache:
            del self.cache[key]
            print(f"[Evento] Chave {key} invalidada.")

    def update_db(self, key, value):
        self.db[key] = value
        self.invalidate(key)

# Teste de Consistência
cache = DistributedCache()
print(f"Leitura inicial: {cache.get('user:1')}")
cache.update_db('user:1', 'Versao_Atualizada')
print(f"Leitura pós-invalidação: {cache.get('user:1')}")

# Verificação de Stampede
def concurrent_read():
    print(f"Leitura paralela: {cache.get('user:1')}")

t1 = threading.Thread(target=concurrent_read)
t2 = threading.Thread(target=concurrent_read)
t1.start(); t2.start()
t1.join(); t2.join()