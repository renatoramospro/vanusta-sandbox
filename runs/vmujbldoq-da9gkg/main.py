import hashlib
import bisect
import statistics

class SecureConsistentHash:
    def __init__(self, nodes=None, replicas=100):
        if not isinstance(replicas, int) or replicas <= 0:
            raise ValueError("O número de réplicas deve ser um inteiro positivo (> 0).")
        
        self.replicas = replicas
        self.ring = []            # Lista ordenada de hashes das posições (int)
        self.ring_map = {}        # Mapeia hash -> lista de nós reais (tratar colisões)
        self.nodes = set()
        
        if nodes:
            for node in nodes:
                self.add_node(node)

    def _hash(self, key: str) -> int:
        """Gera um inteiro de 32 bits usando SHA-256 para maior segurança contra colisões."""
        if not isinstance(key, str) or not key.strip():
            raise TypeError("A chave deve ser uma string não vazia.")
        
        # Usa SHA-256 truncado para 32 bits (0 a 2^32 - 1)
        digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
        return int(digest, 16) & 0xFFFFFFFF

    def add_node(self, node: str):
        """Adiciona um nó real e suas respectivas réplicas virtuais ao anel de forma segura."""
        if not isinstance(node, str) or not node.strip():
            raise TypeError("O identificador do nó deve ser uma string não vazia.")
        if node in self.nodes:
            return  # Evita duplicação silenciosa
        
        self.nodes.add(node)
        for i in range(self.replicas):
            virtual_key = f"{node}-replica-{i}"
            h = self._hash(virtual_key)
            
            # Tratamento de colisão: se o hash já existe no anel, adicionamos à lista de mapeamento
            if h not in self.ring_map:
                bisect.insort(self.ring, h)
                self.ring_map[h] = []
            
            if node not in self.ring_map[h]:
                self.ring_map[h].append(node)

    def remove_node(self, node: str):
        """Remove um nó real e todas as suas réplicas virtuais do anel de forma segura."""
        if not isinstance(node, str) or not node.strip():
            raise TypeError("O identificador do nó deve ser uma string não vazia.")
        if node not in self.nodes:
            return
        
        self.nodes.remove(node)
        
        hashes_to_remove = []
        for h in list(self.ring_map.keys()):
            # Remove o nó da lista de mapeamento deste hash
            self.ring_map[h] = [n for n in self.ring_map[h] if n != node]
            # Se o hash ficou sem nenhum nó associado, remove do anel
            if not self.ring_map[h]:
                hashes_to_remove.append(h)
                del self.ring_map[h]
        
        # Reconstrói a lista ordenada do anel removendo os hashes órfãos
        if hashes_to_remove:
            self.ring = [h for h in self.ring if h not in set(hashes_to_remove)]

    def get_node(self, key: str) -> str:
        """Encontra o nó responsável pela chave usando busca binária O(log V)."""
        if not self.ring:
            raise ValueError("O anel de hash está vazio.")
        
        h = self._hash(key)
        idx = bisect.bisect_right(self.ring, h)
        
        if idx == len(self.ring):
            idx = 0
            
        # Em caso de colisão perfeita de hash, retorna o primeiro nó da lista de forma determinística
        target_hash = self.ring[idx]
        return self.ring_map[target_hash][0]

def run_simulation():
    initial_nodes = ["node-A", "node-B", "node-C", "node-D", "node-E"]
    ch = SecureConsistentHash(nodes=initial_nodes, replicas=150)

    # Gerar 10.000 chaves sintéticas
    num_keys = 10000
    keys = [f"key-{i}" for i in range(num_keys)]

    # 1. Validar distribuição inicial e desvio padrão
    distribution = {n: 0 for n in initial_nodes}
    initial_mapping = {}
    for k in keys:
        node = ch.get_node(k)
        initial_mapping[k] = node
        distribution[node] += 1

    counts = list(distribution.values())
    mean_val = statistics.mean(counts)
    stdev_val = statistics.stdev(counts)
    cv = (stdev_val / mean_val) * 100

    print(f"[Distribuição Inicial com Nós Virtuais e SHA-256]")
    print(f"Média por nó: {mean_val:.2f} | Desvio Padrão: {stdev_val:.2f} | Coef. Variação: {cv:.2f}%")
    assert cv < 10.0, f"Falha: Coeficiente de variação {cv:.2f}% excede 10%!"
    print("-> SUCESSO: Desvio padrão abaixo de 10% validado.")

    # 2. Adicionar um novo nó ("node-F") e medir redistribuição
    ch.add_node("node-F")
    new_mapping = {k: ch.get_node(k) for k in keys}
    
    changed_keys = sum(1 for k in keys if initial_mapping[k] != new_mapping[k])
    redistribution_pct = (changed_keys / num_keys) * 100
    
    print(f"\n[Adição de Nó - node-F]")
    print(f"Chaves redistribuídas: {changed_keys} ({redistribution_pct:.2f}%)")
    assert redistribution_pct < 25.0, f"Falha: Redistribuição de {redistribution_pct:.2f}% acima de 25%!"
    print("-> SUCESSO: Menos de 25% das chaves redistribuídas na adição.")

    # 3. Teste de Validação de Segurança (Entradas Inválidas e Réplicas)
    print("\n[Validação de Segurança e Entradas]")
    try:
        SecureConsistentHash(replicas=0)
    except ValueError as e:
        print(f"-> SUCESSO: Exceção capturada corretamente para réplicas inválidas: {e}")

    try:
        ch.get_node("")
    except TypeError as e:
        print(f"-> SUCESSO: Exceção capturada corretamente para chave vazia: {e}")

if __name__ == "__main__":
    run_simulation()