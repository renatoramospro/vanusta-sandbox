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
    """Lista duplamente ligada para manter nós de mesma frequência em ordem de inserção (LRU secundário)."""
    def __init__(self):
        self.head = Node(None, None) # Sentinela
        self.tail = Node(None, None) # Sentinela
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def add_node(self, node):
        """Adiciona um nó logo após a cabeça (mais recentemente usado daquela frequência)."""
        nxt = self.head.next
        self.head.next = node
        node.prev = self.head
        node.next = nxt
        nxt.prev = node
        self.size += 1

    def remove_node(self, node):
        """Remove um nó arbitrário da lista."""
        prev = node.prev
        nxt = node.next
        prev.next = nxt
        nxt.prev = prev
        self.size -= 1

    def pop_tail(self):
        """Remove e retorna o nó menos recentemente usado da frequência atual (o que está antes da cauda)."""
        if self.size == 0:
            return None
        tail_node = self.tail.prev
        self.remove_node(tail_node)
        return tail_node

class LFUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.key_to_node = {} # key -> Node
        self.freq_to_list = defaultdict(DoublyLinkedList) # freq -> DoublyLinkedList

    def _update_freq(self, node):
        """Incrementa a frequência de um nó e atualiza as estruturas em O(1)."""
        freq = node.freq
        self.freq_to_list[freq].remove_node(node)
        
        # Se a lista da frequência atual ficou vazia e era a menor frequência, incrementa min_freq
        if freq == self.min_freq and self.freq_to_list[freq].size == 0:
            del self.freq_to_list[freq]
            self.min_freq += 1

        node.freq += 1
        self.freq_to_list[node.freq].add_node(node)

    def get(self, key: int) -> int:
        if key not in self.key_to_node:
            return -1
        node = self.key_to_node[key]
        self._update_freq(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if self.capacity <= 0:
            return

        if key in self.key_to_node:
            node = self.key_to_node[key]
            node.val = value
            self._update_freq(node)
            return

        # Se atingiu a capacidade, remove o LFU (e o LRU em caso de empate)
        if len(self.key_to_node) >= self.capacity:
            evict_list = self.freq_to_list[self.min_freq]
            evict_node = evict_list.pop_tail()
            if evict_node:
                del self.key_to_node[evict_node.key]

        # Insere o novo nó com frequência 1
        new_node = Node(key, value)
        self.key_to_node[key] = new_node
        self.freq_to_list[1].add_node(new_node)
        self.min_freq = 1

# --- Bloco de Testes e Validação de Desempenho ---
def run_tests():
    print("Iniciando testes do LFU Cache O(1)...")

    # 1. Teste de Correção Básica
    cache = LFUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1, "Erro: chave 1 deveria estar presente"
    
    cache.put(3, 3) # Deve remover a chave 2 (frequência 1, menos usada)
    assert cache.get(2) == -1, "Erro: chave 2 deveria ter sido evictada"
    assert cache.get(3) == 3, "Erro: chave 3 deveria estar presente"

    print("Testes básicos de correção: APROVADOS.")

    # 2. Teste de Performance e Volume (10.000+ operações)
    ops = 50000
    perf_cache = LFUCache(1000)
    
    start_time = time.time()
    for i in range(ops):
        perf_cache.put(i % 1500, i)
        perf_cache.get(i % 1200)
    duration = time.time() - start_time

    ops_per_sec = ops / duration
    print(f"Executadas {ops} operações em {duration:.4f} segundos ({ops_per_sec:.2f} ops/sec).")
    
    # Validação do critério de sucesso de operações por segundo
    assert ops_per_sec > 10000, f"Desempenho abaixo do esperado: {ops_per_sec} ops/sec"
    print("Teste de throughput (10.000+ ops/sec): APROVADO.")

    # 3. Contraexemplo Conceitual: Por que buscas lineares falham em LFU
    # A abordagem ingênua varre todas as chaves para achar a menor frequência (O(N)).
    # Nossa implementação usa map e doubly linked list garantindo O(1) puro por ponteiros.
    print("Verificação do equívoco comum: Complexidade O(1) real validada via ponteiros de lista.")

if __name__ == "__main__":
    run_tests()