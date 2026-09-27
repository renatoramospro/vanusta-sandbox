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
        """Adiciona um nó real e suas respectivas réplicas virtuais ao anel."""
        if node in self.nodes:
            return
        self.nodes.add(node)
        for i in range(self.replicas):
            virtual_key = f"{node}-replica-{i}"
            h = self._hash(virtual_key)
            bisect.insort(self.ring, h)
            self.ring_map[h] = node

    def remove_node(self, node: str):
        """Remove um nó real e todas as suas réplicas virtuais do anel."""
        if node not in self.nodes:
            return
        self.nodes.remove(node)
        self.ring = [h for h in self.ring if self.ring_map[h] != node]
        for h in list(self.ring_map.keys()):
            if self.ring_map[h] == node:
                del self.ring_map[h]

    def get_node(self, key: str) -> str:
        """Encontra o nó responsável pela chave usando busca binária O(log V)."""
        if not self.ring:
            raise ValueError("O anel de hash está vazio.")
        
        h = self._hash(key)
        idx = bisect.bisect_right(self.ring, h)
        
        # Se o hash for maior que o último ponto, faz o wrap-around para o primeiro
        if idx == len(self.ring):
            idx = 0
            
        return self.ring_map[self.ring[idx]]

def run_simulation():
    initial_nodes = ["node-A", "node-B", "node-C", "node-D", "node-E"]
    ch = ConsistentHash(nodes=initial_nodes, replicas=150)

    # Gerar 10.000 chaves sintéticas
    num_keys = 10000
    keys = [f"key-{i}" for i in range(num_keys)]

    # Mapeamento inicial
    initial_mapping = {k: ch.get_node(k) for k in keys}

    # 1. Validar desvio padrão / coeficiente de variação (< 10%)
    distribution = {n: 0 for n in initial_nodes}
    for k in keys:
        distribution[ch.get_node(k)] += 1

    counts = list(distribution.values())
    mean_val = statistics.mean(counts)
    stdev_val = statistics.stdev(counts)
    cv = (stdev_val / mean_val) * 100

    print(f"[Distribuição Inicial com Nós Virtuais]")
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