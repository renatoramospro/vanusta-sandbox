path=consistent_hashing.py
import hashlib
import bisect
import statistics

class ConsistentHash:
    def __init__(self, nodes=None, replicas=100):
        self.replicas = replicas  # Número de nós virtuais por nó real
        self.ring = []            # Lista ordenada de hashes das posições (int)
        self.ring_map = {}        # Mapeia hash do nó virtual -> nome do nó real
        self.nodes = set()
        
        if nodes:
            for node in nodes:
                self.add_node(node)

    def _hash(self, key: str) -> int:
        """Gera um inteiro de 32 bits usando MD5."""
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16) & 0xFFFFFFFF

    def add_node(self, node: str):
        """Adiciona um nó real ao anel com múltiplos nós virtuais."""
        if node in self.nodes:
            return
        self.nodes.add(node)
        for i in range(self.replicas):
            virtual_key = f"{node}-vnode-{i}"
            h = self._hash(virtual_key)
            bisect.insort(self.ring, h)
            self.ring_map[h] = node

    def remove_node(self, node: str):
        """Remove um nó real e todos os seus nós virtuais do anel."""
        if node not in self.nodes:
            return
        self.nodes.remove(node)
        new_ring = []
        new_ring_map = {}
        for h in self.ring:
            if self.ring_map[h] != node:
                new_ring.append(h)
                new_ring_map[h] = self.ring_map[h]
            else:
                del self.ring_map[h]
        self.ring = new_ring
        self.ring_map = new_ring_map

    def get_node(self, key: str) -> str:
        """Retorna o nó responsável pela chave com complexidade O(log V)."""
        if not self.ring:
            raise ValueError("Anel de hash vazio.")
        h = self._hash(key)
        idx = bisect.bisect(self.ring, h)
        if idx == len(self.ring):
            idx = 0
        return self.ring_map[self.ring[idx]]


def run_simulation():
    print("=== INICIANDO SIMULAÇÃO DE CONSISTENT HASHING ===")
    
    # 1. Configuração inicial com 5 nós e 150 réplicas
    initial_nodes = ["node-A", "node-B", "node-C", "node-D", "node-E"]
    ch = ConsistentHash(nodes=initial_nodes, replicas=150)
    
    # Gerar 10.000 chaves de teste
    num_keys = 10000
    keys = [f"user_session_{i}" for i in range(num_keys)]
    
    # Mapear chaves iniciais
    initial_mapping = {k: ch.get_node(k) for k in keys}
    
    # Contar distribuição inicial
    distribution = {n: 0 for n in initial_nodes}
    for k, n in initial_mapping.items():
        distribution[n] += 1
        
    counts = list(distribution.values())
    mean_val = statistics.mean(counts)
    stdev_val = statistics.stdev(counts)
    cv = (stdev_val / mean_val) * 100
    
    print(f"\n[Distribuição Inicial - 5 nós]")
    print(f"Média por nó: {mean_val:.2f} | Desvio Padrão: {stdev_val:.2f} | Coef. Variação: {cv:.2f}%")
    assert cv < 10.0, f"Falha: Coeficiente de variação {cv:.2f}% excede 10%!"
    print("-> SUCESSO: Desvio padrão abaixo de 10% validado com nós virtuais.")

    # 2. Adicionar um novo nó ("node-F") e medir redistribuição
    ch.add_node("node-F")
    new_mapping = {k: ch.get_node(k) for k in keys}
    
    changed_keys = sum(1 for k in keys if initial_mapping[k] != new_mapping[k])
    redistribution_pct = (changed_keys / num_keys) * 100
    
    print(f"\n[Adição de Nó - node-F]")
    print(f"Chaves redistribuídas: {changed_keys} ({redistribution_pct:.2f}%)")
    assert redistribution_pct < 25.0, f"Falha: Redistribuição de {redistribution_pct:.2f}% acima de 25%!"
    print("-> SUCESSO: Menos de 25% das chaves redistribuídas na adição.")

    # 3. CONTRAEXEMPLO: Demonstrar o problema sem nós virtuais (replicas = 1)
    print("\n[CONTRAEXEMPLO: Sem nós virtuais (replicas=1)]")
    bad_ch = ConsistentHash(nodes=initial_nodes, replicas=1)
    bad_dist = {n: 0 for n in initial_nodes}
    for k in keys:
        bad_dist[bad_ch.get_node(k)] += 1
    bad_counts = list(bad_dist.values())
    bad_stdev = statistics.stdev(bad_counts)
    bad_mean = statistics.mean(bad_counts)
    bad_cv = (bad_stdev / bad_mean) * 100
    print(f"Sem nós virtuais - Coef. Variação: {bad_cv:.2f}% (Geralmente > 30-50%, falhando no critério de 10%)")
    print("-> Justificativa: Sem nós virtuais, a granularidade do hash é baixa, gerando aglomerados e hotspots graves.")

if __name__ == "__main__":
    run_simulation()