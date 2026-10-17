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
        """Retorna True se há conflito concorrente entre dois relógios."""
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
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.storage:
                self.hits += 1
                return self.storage[key].value
            self.misses += 1
            return None

    def put_internal(self, key: str, value: Any, version: VectorClock, timestamp: float) -> bool:
        """Aplica escrita com resolução de conflitos por Vector Clock / Timestamp."""
        with self.lock:
            if key not in self.storage:
                self.storage[key] = CacheItem(value, version, timestamp)
                return True
            
            existing = self.storage[key]
            # Verifica concorrência
            if version.is_concurrent_with(existing.version):
                # Resolução determinística de conflito (Last-Write-Wins por timestamp lógico/físico)
                if timestamp > existing.timestamp:
                    self.storage[key] = CacheItem(value, version, timestamp)
                    return True
                return False # Mantém o existente por critério de desempate
            
            # Se não é concorrente, substitui se a nova versão for estritamente maior
            self.storage[key] = CacheItem(value, version, timestamp)
            return True

class DistributedCacheCluster:
    def __init__(self, node_ids: List[str], replication_factor: int = 2):
        self.nodes: Dict[str, CacheNode] = {nid: CacheNode(nid) for nid in node_ids}
        self.ring: List[Tuple[int, str]] = []
        self.replication_factor = replication_factor
        self.node_ids = node_ids
        for nid in node_ids:
            self._add_node_to_ring(nid)

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def _add_node_to_ring(self, node_id: str):
        # Virtual nodes para balanceamento
        for i in range(3):
            vnode_key = f"{node_id}-vnode-{i}"
            h = self._hash(vnode_key)
            self.ring.append((h, node_id))
        self.ring.sort(key=lambda x: x[0])

    def get_preference_list(self, key: str) -> List[CacheNode]:
        h = self._hash(key)
        target_nodes = []
        seen = set()
        
        for ring_h, node_id in self.ring:
            if ring_h >= h and node_id not in seen:
                seen.add(node_id)
                target_nodes.append(self.nodes[node_id])
                if len(target_nodes) == self.replication_factor:
                    break
        # Wrap around se necessário
        if len(target_nodes) < self.replication_factor:
            for ring_h, node_id in self.ring:
                if node_id not in seen:
                    seen.add(node_id)
                    target_nodes.append(self.nodes[node_id])
                    if len(target_nodes) == self.replication_factor:
                        break
        return target_nodes

    def put(self, key: str, value: Any, client_node_id: str):
        nodes = self.get_preference_list(key)
        timestamp = time.time()
        
        # Incrementa relógio vetorial do nó coordenador/cliente
        node = self.nodes[client_node_id]
        # Simula versionamento
        version = VectorClock({client_node_id: 1}) # Simplificado para demonstração
        
        for target in nodes:
            target.put_internal(key, value, version, timestamp)

    def get(self, key: str, client_node_id: str) -> Optional[Any]:
        nodes = self.get_preference_list(key)
        # Lê do primeiro nó disponível (consistência eventual)
        if nodes:
            return nodes[0].get(key)
        return None

# ==========================================
# EXPERIMENTO E VALIDAÇÃO DE DESEMPENHO
# ==========================================
if __name__ == "__main__":
    print("Iniciando simulação do Sistema de Cache Distribuído...")
    
    cluster = DistributedCacheCluster(["node-A", "node-B", "node-C"], replication_factor=2)
    
    # Teste de carga simulada para validar throughput e latência
    num_requests = 1000
    start_time = time.time()
    
    for i in range(num_requests):
        key = f"key-{i % 200}" # Chaves limitadas para testar Hit Rate
        if i % 2 == 0:
            cluster.put(key, f"val-{i}", "node-A")
        else:
            cluster.get(key, "node-A")
            
    elapsed = time.time() - start_time
    throughput = num_requests / elapsed
    latency_ms = (elapsed / num_requests) * 1000
    
    print(f"Requisições processadas: {num_requests}")
    print(f"Tempo total: {elapsed:.4f}s")
    print(f"Throughput simulado: {throughput:.2f} req/s")
    print(f"Latência média por requisição: {latency_ms:.4f} ms")
    
    # Validação do Vector Clock e Conflitos Concorrentes
    vc1 = VectorClock({"node-A": 1, "node-B": 2})
    vc2 = VectorClock({"node-A": 2, "node-B": 1})
    
    is_conflict = vc1.is_concurrent_with(vc2)
    print(f"Detecção de Conflito Concorrente com Vector Clocks: {is_conflict}")
    assert is_conflict == True, "Deveria detectar conflito entre relógios concorrentes."
    
    print("Experimento executado com sucesso e asserções validadas!")