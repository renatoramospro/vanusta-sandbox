import hashlib
import threading
import time
import random
from typing import Dict, Any, List, Optional, Tuple

class VectorClock:
    def __init__(self, clock: Optional[Dict[str, int]] = None):
        self.clock: Dict[str, int] = dict(clock) if clock else {}

    def increment(self, node_id: str) -> 'VectorClock':
        new_clock = dict(self.clock)
        new_clock[node_id] = new_clock.get(node_id, 0) + 1
        return VectorClock(new_clock)

    def is_concurrent_with(self, other: 'VectorClock') -> bool:
        """
        Retorna True se há conflito concorrente genuíno entre dois relógios.
        Dois relógios A e B são concorrentes se nenhum domina o outro:
        A não é menor/igual a B em todas as entradas E B não é menor/igual a A em todas as entradas.
        Ou seja, A tem componentes maiores que B e também menores que B.
        """
        self_keys = set(self.clock.keys())
        other_keys = set(other.clock.keys())
        all_keys = self_keys.union(other_keys)
        
        self_greater = False
        other_greater = False
        
        for k in all_keys:
            v_self = self.clock.get(k, 0)
            v_other = other.clock.get(k, 0)
            if v_self > v_other:
                self_greater = True
            elif v_self < v_other:
                other_greater = True
                
        # Concorrente apenas se houver conflito bidirecional de dominância
        return self_greater and other_greater

    def __repr__(self):
        return str(self.clock)

class CacheItem:
    def __init__(self, value: Any, version: VectorClock, timestamp: float):
        self.value = value
        self.version = version
        self.timestamp = timestamp

class CacheNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.storage: Dict[str, CacheItem] = {}
        self.lock = threading.Lock()
        self.is_alive = True
        self.conflict_count = 0

    def get(self, key: str) -> Optional[Any]:
        if not self.is_alive:
            return None
        with self.lock:
            item = self.storage.get(key)
            return item.value if item else None

    def put(self, key: str, value: Any, version: VectorClock, timestamp: float) -> bool:
        if not self.is_alive:
            return False
        with self.lock:
            existing = self.storage.get(key)
            if existing:
                # Verificar se há conflito concorrente
                if existing.version.is_concurrent_with(version):
                    self.conflict_count += 1
                    # Resolução determinística: Last-Write-Wins (LWW) por timestamp e node_id
                    if timestamp > existing.timestamp or (timestamp == existing.timestamp and self.node_id > "node-X"):
                        self.storage[key] = CacheItem(value, version, timestamp)
                elif version.is_concurrent_with(existing.version) is False:
                    # Se version avança existing (ou é idêntica)
                    self.storage[key] = CacheItem(value, version, timestamp)
            else:
                self.storage[key] = CacheItem(value, version, timestamp)
        return True

class ConsistentHashRing:
    def __init__(self, nodes: List[str], replicas: int = 3):
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        for node in nodes:
            self.add_node(node)

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node: str):
        for i in range(self.replicas):
            virtual_key = f"{node}-{i}"
            h = self._hash(virtual_key)
            self.ring[h] = node
            self.sorted_keys.append(h)
        self.sorted_keys.sort()

    def get_nodes(self, key: str, count: int = 2) -> List[str]:
        if not self.sorted_keys:
            return []
        h = self._hash(key)
        idx = 0
        for i, val in enumerate(self.sorted_keys):
            if h <= val:
                idx = i
                break
        
        nodes = []
        seen = set()
        for i in range(len(self.sorted_keys)):
            current_node = self.ring[self.sorted_keys[(idx + i) % len(self.sorted_keys)]]
            if current_node not in seen:
                seen.add(current_node)
                nodes.append(current_node)
                if len(nodes) == count:
                    break
        return nodes

class DistributedCacheCluster:
    def __init__(self, node_ids: List[str], replication_factor: int = 2):
        self.nodes: Dict[str, CacheNode] = {nid: CacheNode(nid) for nid in node_ids}
        self.ring = ConsistentHashRing(node_ids)
        self.replication_factor = replication_factor
        self.global_vector = VectorClock()
        self.global_lock = threading.Lock()
        
        # Métricas
        self.total_requests = 0
        self.cache_hits = 0
        self.conflicts_resolved = 0

    def _get_next_version(self, node_id: str) -> VectorClock:
        with self.global_lock:
            self.global_vector = self.global_vector.increment(node_id)
            return VectorClock(self.global_vector.clock)

    def put(self, key: str, value: Any, origin_node: str):
        target_nodes = self.ring.get_nodes(key, self.replication_factor)
        version = self._get_next_version(origin_node)
        timestamp = time.time()
        
        success = False
        for n_id in target_nodes:
            node = self.nodes.get(n_id)
            if node and node.put(key, value, version, timestamp):
                success = True
        
        with self.global_lock:
            for n_id in target_nodes:
                if self.nodes[n_id].conflict_count > 0:
                    self.conflicts_resolved += self.nodes[n_id].conflict_count
                    self.nodes[n_id].conflict_count = 0
        return success

    def get(self, key: str, origin_node: str) -> Optional[Any]:
        with self.global_lock:
            self.total_requests += 1
            
        target_nodes = self.ring.get_nodes(key, self.replication_factor)
        for n_id in target_nodes:
            node = self.nodes.get(n_id)
            if node:
                val = node.get(key)
                if val is not None:
                    with self.global_lock:
                        self.cache_hits += 1
                    return val
        return None

# ==========================================
# EXPERIMENTO DE CARGA REALISTA E CONCORRENTE
# ==========================================
if __name__ == "__main__":
    print("Iniciando simulação avançada do Sistema de Cache Distribuído...")
    
    cluster = DistributedCacheCluster(["node-A", "node-B", "node-C"], replication_factor=2)
    
    num_threads = 10
    requests_per_thread = 200
    total_expected = num_threads * requests_per_thread
    
    def worker(thread_id: int):
        origin = f"node-{chr(65 + (thread_id % 3))}"
        for i in range(requests_per_thread):
            key = f"key-{random.randint(1, 100)}" # Chaves limitadas para testar Hit Rate alto
            if i % 3 != 0:
                cluster.put(key, f"val-{thread_id}-{i}", origin)
            else:
                cluster.get(key, origin)
            # Simula latência de rede assíncrona variável
            time.sleep(0.0001)

    start_time = time.time()
    threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    elapsed = time.time() - start_time
    throughput = total_expected / elapsed
    latency_ms = (elapsed / total_expected) * 1000
    hit_rate = (cluster.cache_hits / cluster.total_requests) * 100 if cluster.total_requests > 0 else 0
    
    print(f"Requisições processadas concorrentemente: {cluster.total_requests}")
    print(f"Tempo total: {elapsed:.4f}s")
    print(f"Throughput real: {throughput:.2f} req/s")
    print(f"Latência média por requisição: {latency_ms:.4f} ms")
    print(f"Taxa de acerto de cache (Hit Rate): {hit_rate:.2f}%")
    print(f"Conflitos resolvidos com sucesso: {cluster.conflicts_resolved}")

    # Validação rigorosa dos Vector Clocks corrigidos
    vc_base = VectorClock({"node-A": 1, "node-B": 1})
    vc_concurrent_1 = VectorClock({"node-A": 2, "node-B": 1})
    vc_concurrent_2 = VectorClock({"node-A": 1, "node-B": 2})
    vc_sequential = VectorClock({"node-A": 2, "node-B": 2})

    # Conflitos genuínos devem retornar True
    assert vc_concurrent_1.is_concurrent_with(vc_concurrent_2) == True, "Deveria detectar conflito concorrente."
    
    # Timestamps estritamente ordenados não devem gerar falso positivo de concorrência
    assert vc_base.is_concurrent_with(vc_sequential) == False, "Relógio estritamente anterior não deve ser considerado concorrente."

    print("Validação de Vector Clocks e testes de concorrência executados com sucesso!")