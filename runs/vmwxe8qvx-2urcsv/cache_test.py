import random
from collections import OrderedDict, Counter
import math

# --- 1. Geração de Acessos de Zipf ---
def generate_zipf_sequence(N=1000, alpha=1.5):
    """Gera uma sequência de N chaves baseada na distribuição de Zipf."""
    # Gera N chaves únicas (1 a N)
    keys = list(range(1, N + 1))
    # Ponderação de Zipf: P(k) ~ 1 / k^alpha
    weights = [1 / (k**alpha) for k in keys]
    # Seleciona N acessos com base nas probabilidades
    sequence = random.choices(keys, weights=weights, k=N)
    return sequence

# --- 2. Implementação LRU ---
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        # OrderedDict mantém a ordem de inserção/movimentação
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return None
        # Move o item para o final (mais recentemente usado)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            # Remove o primeiro item (menos recentemente usado)
            self.cache.popitem(last=False)

# --- 3. Implementação LFU ---
class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.key_to_freq = {}  # Mapeia chave -> frequência
        self.freq_map = {}    # Mapeia frequência -> set de chaves
        self.min_freq = 0     # Frequência mínima existente
        self.cache = {}       # Mapeia chave -> valor (para armazenar o dado)

    def _update_freq(self, key):
        old_freq = self.key_to_freq[key]
        new_freq = old_freq + 1
        
        # 1. Remover chave do antigo set de frequência
        self.freq_map[old_freq].remove(key)
        
        # 2. Se o antigo set ficou vazio, e era a frequência mínima, atualiza min_freq
        if not self.freq_map[old_freq]:
            del self.freq_map[old_freq]
            if old_freq == self.min_freq:
                self.min_freq = new_freq
        
        # 3. Adicionar chave ao novo set de frequência
        if new_freq not in self.freq_map:
            self.freq_map[new_freq] = set()
        self.freq_map[new_freq].add(key)
        
        # 4. Atualizar mapeamentos
        self.key_to_freq[key] = new_freq

    def get(self, key):
        if key not in self.cache:
            return None
        self._update_freq(key)
        return self.cache[key]

    def put(self, key, value):
        if self.capacity == 0:
            return
            
        if key in self.cache:
            # Atualiza valor e frequência se já existe
            self.cache[key] = value
            self._update_freq(key)
            return

        # Novo item
        if len(self.cache) >= self.capacity:
            # Evicção: remove um item da frequência mínima
            key_to_evict = self.freq_map[self.min_freq].pop()
            del self.cache[key_to_evict]
            del self.key_to_freq[key_to_evict]
            
            # Se o set da min_freq ficou vazio, remove a entrada de frequência
            if not self.freq_map[self.min_freq]:
                del self.freq_map[self.min_freq]
                # Nota: min_freq será ajustado no próximo put/get se houver novos itens

        # Inserção do novo item
        self.cache[key] = value
        self.key_to_freq[key] = 1
        
        # Inicializa a frequência 1
        if 1 not in self.freq_map:
            self.freq_map[1] = set()
        self.freq_map[1].add(key)
        
        # A frequência mínima é sempre 1 após uma inserção
        self.min_freq = 1


def simulate_cache(cache_instance, access_sequence, capacity):
    hits = 0
    for key in access_sequence:
        if cache_instance.get(key) is not None:
            hits += 1
        # Para simular o comportamento de PUT em um cenário de acesso, 
        # assumimos que se o item não está, ele é inserido (PUT).
        if cache_instance.get(key) is None:
             # Simula inserção se for um miss
             cache_instance.put(key, f"value_{key}")
             
    return hits

# --- Execução Principal ---
CAPACITY = 10
ACCESS_SEQUENCE = generate_zipf_sequence(N=1000, alpha=1.5)

# Teste LRU
lru_cache = LRUCache(CAPACITY)
lru_hits = simulate_cache(lru_cache, ACCESS_SEQUENCE, CAPACITY)
lru_hit_rate = lru_hits / 1000.0

# Teste LFU
lfu_cache = LFUCache(CAPACITY)
lfu_hits = simulate_cache(lfu_cache, ACCESS_SEQUENCE, CAPACITY)
lfu_hit_rate = lfu_hits / 1000.0

print(f"--- Simulação de Cache (Capacidade={CAPACITY}, Acessos=1000, Zipf alpha=1.5) ---")
print(f"LRU Hits: {lru_hits}, Hit Rate: {lru_hit_rate:.4f}")
print(f"LFU Hits: {lfu_hits}, Hit Rate: {lfu_hit_rate:.4f}")

# Verificação do Critério de Sucesso
success_lru = lru_hit_rate > 0.85
success_lfu = lfu_hit_rate > 0.85

print(f"\nLRU atende critério (> 85%): {success_lru}")
print(f"LFU atende critério (> 85%): {success_lfu}")

# Garantir que o experimento termina com código 0
# O critério de sucesso exige que PELO MENOS UMA política atinja 85%
assert success_lru or success_lfu, "Nenhuma política atingiu o critério de 85%."