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
        self.cache = {}  # key -> (value, count)
        self.freq_map = Counter() # count -> set_of_keys
        self.min_freq = 0

    def _update_freq(self, key, value):
        old_count = self.freq_map[self.cache[key][0]]
        
        # 1. Remove key do antigo bucket de frequência
        self.freq_map[old_count].remove(key)
        if not self.freq_map[old_count]:
            del self.freq_map[old_count]
            # Se o bucket de frequência mínima ficou vazio, atualiza min_freq
            if old_count == self.min_freq:
                self.min_freq += 1
        
        # 2. Incrementa e adiciona ao novo bucket
        new_count = old_count + 1
        self.freq_map[new_count].add(key)
        
        # 3. Atualiza o cache e min_freq
        self.cache[key] = (value, new_count)
        if new_count == 1 and self.min_freq == 0:
            self.min_freq = 1

    def get(self, key):
        if key not in self.cache:
            return None
        # Atualiza frequência (complexidade O(1) amortizado)
        self._update_freq(key, self.cache[key][0])
        return self.cache[key][0]

    def put(self, key, value):
        if key in self.cache:
            # Atualiza valor e frequência
            self.cache[key] = (value, self.cache[key][1]) # Mantém o valor antigo para o update
            self._update_freq(key, value)
            return

        if len(self.cache) >= self.capacity:
            # Evicção: remove um item com a frequência mínima
            keys_to_evict = self.freq_map[self.min_freq]
            key_to_evict = keys_to_evict.pop()
            del self.cache[key_to_evict]
            if not keys_to_evict:
                del self.freq_map[self.min_freq]
            
        # Novo item
        self.cache[key] = (value, 1)
        self.freq_map[1].add(key)
        self.min_freq = 1


# --- 4. Simulação e Avaliação ---
def simulate_cache(cache_instance, access_sequence, capacity):
    hits = 0
    for key in access_sequence:
        if cache_instance.get(key) is not None:
            hits += 1
        # Para simular o comportamento de PUT em um cenário de acesso, 
        # assumimos que se o item não está, ele é inserido (PUT).
        # Para simplificar a métrica de hit rate, focamos apenas no GET.
        # Se o GET falhar, o PUT subsequente o adicionará.
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
assert lru_hit_rate > 0.85 or lfu_hit_rate > 0.85, "Nenhuma política atingiu o critério de 85%."