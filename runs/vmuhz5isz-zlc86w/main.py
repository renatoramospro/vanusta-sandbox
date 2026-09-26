import time
from collections import defaultdict

class Node:
    """Nó da lista duplamente ligada para armazenar chave, valor e frequência."""
    __slots__ = ('key', 'val', 'freq', 'prev', 'next')
    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.freq = 1
        self.prev = None
        self.next = None

class DoublyLinkedList:
    """Lista duplamente ligada para manter nós de mesma frequência em ordem de recência."""
    def __init__(self):
        self.head = Node(None, None)
        self.tail = Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def add_node(self, node):
        nxt = self.head.next
        self.head.next = node
        node.prev = self.head
        node.next = nxt
        nxt.prev = node
        self.size += 1

    def remove_node(self, node):
        prev = node.prev
        nxt = node.next
        prev.next = nxt
        nxt.prev = prev
        self.size -= 1

    def pop_tail(self):
        if self.size == 0:
            return None
        node = self.tail.prev
        self.remove_node(node)
        return node

class LFUCache:
    """
    Cache LFU com complexidade esperada O(1) para get e put.
    Nota: O(1) é esperado/amortizado devido à dependência do dicionário Python (tabela hash).
    """
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.key_to_node = {}
        self.freq_to_nodes = defaultdict(DoublyLinkedList)

    def _update_freq(self, node):
        freq = node.freq
        self.freq_to_nodes[freq].remove_node(node)
        
        if freq == self.min_freq and self.freq_to_nodes[freq].size == 0:
            self.min_freq += 1
            
        node.freq += 1
        self.freq_to_nodes[node.freq].add_node(node)

    def get(self, key: int) -> int:
        if key not in self.key_to_node:
            return -1
        node = self.key_to_node[key]
        self._update_freq(node)
        return node.val

    def put(self, key: int, value: int) -> void:
        if self.capacity <= 0:
            return

        if key in self.key_to_node:
            node = self.key_to_node[key]
            node.val = value
            self._update_freq(node)
            return

        if len(self.key_to_node) >= self.capacity:
            # Remove o menos frequentemente usado (e menos recentemente usado em caso de empate)
            lru_list = self.freq_to_nodes[self.min_freq]
            to_remove = lru_list.pop_tail()
            if to_remove:
                del self.key_to_node[to_remove.key]

        # Insere novo nó
        new_node = Node(key, value)
        self.key_to_node[key] = new_node
        self.freq_to_nodes[1].add_node(new_node)
        self.min_freq = 1

def run_tests():
    print("Iniciando testes rigorosos do LFU Cache...")

    # 1. Testes básicos de correção
    cache = LFUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3) # Deve remover a chave 2 (freq 1, LRU)
    assert cache.get(2) == -1
    assert cache.get(3) == 3
    print("Testes básicos de correção: APROVADOS.")

    # 2. Benchmark de Throughput e contagem correta de operações
    iterations = 50000
    total_operations = iterations * 2  # Cada iteração faz 1 put e 1 get
    perf_cache = LFUCache(1000)
    
    start_time = time.time()
    for i in range(iterations):
        perf_cache.put(i % 1500, i)
        perf_cache.get(i % 1200)
    duration = time.time() - start_time

    ops_per_sec = total_operations / duration
    print(f"Executadas {iterations} iterações ({total_operations} operações totais) em {duration:.4f} segundos ({ops_per_sec:.2f} ops/sec).")
    assert ops_per_sec > 10000, f"Desempenho abaixo do esperado: {ops_per_sec} ops/sec"
    print("Teste de throughput (10.000+ ops/sec): APROVADO.")

    # 3. Medição explícita de Hit Rate (> 90%)
    hit_cache = LFUCache(100)
    # Popular o cache inicialmente
    for i in range(100):
        hit_cache.put(i, i * 10)
    
    hits = 0
    total_lookups = 10000
    # Cenário de acesso repetitivo (80% dos acessos focados em 20% das chaves)
    for i in range(total_lookups):
        key = (i % 20) if (i % 10 < 9) else (i % 100)
        if hit_cache.get(key) != -1:
            hits += 1
            
    hit_rate = (hits / total_lookups) * 100
    print(f"Taxa de acerto (Hit Rate) medida: {hit_rate:.2f}%")
    assert hit_rate > 90.0, f"Hit rate insuficiente: {hit_rate}%"
    print("Teste de Taxa de Acerto (>90%): APROVADO.")

    print("Nota teórica: A complexidade O(1) é esperada/amortizada, dependente da garantia de hash do dicionário Python.")

if __name__ == "__main__":
    run_tests()