import time
import hashlib
import statistics

class ShardNode:
    def __init__(self, shard_id):
        self.shard_id = shard_id
        self.data = {}
        self.write_count = 0
        self.read_count = 0

    def insert(self, key, value):
        # Simula latência de rede/disco (bem abaixo de 100ms)
        time.sleep(0.002) 
        self.data[key] = value
        self.write_count += 1

    def query(self, key):
        time.sleep(0.001)
        self.read_count += 1
        return self.data.get(key, None)

class DatabaseCluster:
    def __init__(self, num_shards=3):
        self.shards = [ShardNode(i) for i in range(num_shards)]
        self.num_shards = num_shards

    def range_route(self, user_id):
        """
        Range Sharding baseado em faixas de ID de usuário:
        Shard 0: 1 a 333
        Shard 1: 334 a 666
        Shard 2: 667 a 1000
        """
        if user_id <= 333:
            return 0
        elif user_id <= 666:
            return 1
        else:
            return 2

    def hash_route(self, user_id):
        """
        Hash Sharding usando MD5 do ID para distribuição uniforme,
        evitando hotspots de chaves sequenciais.
        """
        hash_val = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
        return hash_val % self.num_shards

    def insert_data(self, strategy, key, value):
        start_time = time.time()
        if strategy == "range":
            shard_idx = self.range_route(key)
        elif strategy == "hash":
            shard_idx = self.hash_route(key)
        else:
            raise ValueError("Estratégia desconhecida")
        
        self.shards[shard_idx].insert(key, value)
        latency = (time.time() - start_time) * 1000 # em milissegundos
        return shard_idx, latency

    def query_data(self, strategy, key):
        start_time = time.time()
        if strategy == "range":
            shard_idx = self.range_route(key)
        elif strategy == "hash":
            shard_idx = self.hash_route(key)
        else:
            raise ValueError("Estratégia desconhecida")
            
        val = self.shards[shard_idx].query(key)
        latency = (time.time() - start_time) * 1000
        return shard_idx, latency

def run_simulation():
    print("=== INICIANDO SIMULAÇÃO DE SHARDING (3 Shards) ===")
    
    # --- TESTE 1: HASH SHARDING (Distribuição Uniforme) ---
    cluster_hash = DatabaseCluster(num_shards=3)
    latencies_hash = []
    
    print("\n[1] Executando inserções com HASH SHARDING (chaves sequenciais 1..900)...")
    for i in range(1, 901):
        _, lat = cluster_hash.insert_data("hash", i, f"data_{i}")
        latencies_hash.append(lat)
        
    p95_hash = statistics.quantiles(latencies_hash, n=20)[18] # Aproximação do p95
    print(f"Hash Sharding - Latência Média de Escrita: {statistics.mean(latencies_hash):.2f}ms")
    print(f"Hash Sharding - Latência p95 de Escrita: {p95_hash:.2f}ms (Meta: < 100ms)")
    assert p95_hash < 100, "Falha: Latência p95 acima de 100ms no Hash Sharding!"

    # Validar balanceamento de carga (contagem de registros por shard)
    writes_per_shard = [s.write_count for s in cluster_hash.shards]
    print(f"Carga por Shard (Hash): {writes_per_shard}")
    max_diff_hash = max(writes_per_shard) - min(writes_per_shard)
    print(f"Diferença máxima entre shards (Hash): {max_diff_hash} registros")
    # Com hash bem distribuído, a diferença deve ser pequena (ex: < 10% do total)
    assert max_diff_hash < 150, "Falha: Desbalanceamento excessivo no Hash Sharding!"

    # --- TESTE 2: RANGE SHARDING (Risco de Hotspot vs Eficiência de Range Scan) ---
    cluster_range = DatabaseCluster(num_shards=3)
    latencies_range = []
    
    print("\n[2] Executando inserções com RANGE SHARDING (chaves 1..900)...")
    for i in range(1, 901):
        _, lat = cluster_range.insert_data("range", i, f"data_{i}")
        latencies_range.append(lat)

    p95_range = statistics.quantiles(latencies_range, n=20)[18]
    print(f"Range Sharding - Latência Média de Escrita: {statistics.mean(latencies_range):.2f}ms")
    print(f"Range Sharding - Latência p95 de Escrita: {p95_range:.2f}ms (Meta: < 100ms)")
    assert p95_range < 100, "Falha: Latência p95 acima de 100ms no Range Sharding!"

    writes_per_shard_range = [s.write_count for s in cluster_range.shards]
    print(f"Carga por Shard (Range): {writes_per_shard_range}")
    # Nota conceitual: se inserirmos em ordem estritamente crescente, o Range Sharding 
    # envia tudo para o último shard ativo no momento do preenchimento, demonstrando o hotspot clássico.

    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO! ===")

if __name__ == "__main__":
    run_simulation()