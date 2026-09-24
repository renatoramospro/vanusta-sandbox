import hashlib
import bisect
import time

class ConsistentHashRing:
    """
    Implementação de um anel de Consistent Hashing com nós virtuais
    para garantir uma distribuição uniforme de chaves entre os shards.
    """
    def __init__(self, replicas=32):
        self.replicas = replicas
        self.ring = []  # Lista de tuplas (hash_value, node_name) ordenada
        self.nodes = set()

    def _hash(self, key):
        # Retorna um hash inteiro de 128 bits usando MD5
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node):
        self.nodes.add(node)
        for i in range(self.replicas):
            val = self._hash(f"{node}-replica-{i}")
            bisect.insort(self.ring, (val, node))

    def remove_node(self, node):
        self.nodes.remove(node)
        self.ring = [item for item in self.ring if item[1] != node]

    def get_node(self, key):
        if not self.ring:
            return None
        val = self._hash(key)
        # Encontra o primeiro nó virtual com hash >= hash da chave
        idx = bisect.bisect_right(self.ring, (val, None))
        if idx == len(self.ring):
            idx = 0
        return self.ring[idx][1]


class ShardedDatabaseClient:
    """
    Cliente de Banco de Dados que gerencia múltiplos shards e implementa
    roteamento de dados, Scatter-Gather e migração online (sem downtime).
    """
    def __init__(self, initial_shards, replicas=32):
        self.replicas = replicas
        self.ring = ConsistentHashRing(replicas=replicas)
        self.shards = {}
        
        # Estado de transição para rebalanceamento online
        self.old_ring = None
        self.migrating = False

        for shard_id in initial_shards:
            self.shards[shard_id] = {}  # Banco em memória simulado
            self.ring.add_node(shard_id)

    def put(self, key, value):
        """
        Insere ou atualiza uma chave. Se estiver em migração,
        garante que novas escritas vão para o novo anel.
        """
        shard_id = self.ring.get_node(key)
        self.shards[shard_id][key] = value

    def get(self, key):
        """
        Busca uma chave. Se estiver em migração e a chave não for encontrada
        no novo shard correspondente, busca no shard antigo (evitando downtime).
        """
        shard_id = self.ring.get_node(key)
        val = self.shards[shard_id].get(key)
        
        # Se estiver em migração e não achou no novo shard, tenta no anel antigo
        if val is None and self.migrating and self.old_ring:
            old_shard_id = self.old_ring.get_node(key)
            val = self.shards[old_shard_id].get(key)
            if val is not None:
                # Lazy Migration: move o dado para o novo shard sob demanda
                self.shards[shard_id][key] = val
                del self.shards[old_shard_id][key]
                
        return val

    def add_shard_online(self, new_shard_id):
        """
        Adiciona um novo shard e inicia o processo de migração online (rebalanceamento).
        """
        print(f"\n[SISTEMA] Iniciando adição online do shard: {new_shard_id}")
        self.shards[new_shard_id] = {}
        
        # Salva o anel atual como antigo e ativa o estado de migração
        self.old_ring = ConsistentHashRing(replicas=self.replicas)
        self.old_ring.ring = list(self.ring.ring)
        self.old_ring.nodes = set(self.ring.nodes)
        
        self.migrating = True
        
        # Atualiza o anel principal com o novo nó
        self.ring.add_node(new_shard_id)

    def complete_migration(self):
        """
        Varre os shards antigos e migra ativamente as chaves restantes
        que agora pertencem ao novo anel, finalizando a transição.
        """
        if not self.migrating:
            return
        
        keys_migrated = 0
        # Coleta todas as chaves que precisam mudar de shard
        for shard_id, storage in list(self.shards.items()):
            if shard_id == list(self.shards.keys())[-1]: 
                # Pula o shard recém-adicionado durante a varredura de origem
                continue
            
            keys_to_move = []
            for key in list(storage.keys()):
                target_shard = self.ring.get_node(key)
                if target_shard != shard_id:
                    keys_to_move.append((key, storage[key], target_shard))
            
            for key, val, target in keys_to_move:
                self.shards[target][key] = val
                del self.shards[shard_id][key]
                keys_migrated += 1

        self.migrating = False
        self.old_ring = None
        print(f"[SISTEMA] Migração concluída! {keys_migrated} chaves foram movidas.")

    def scatter_gather_query(self, filter_fn):
        """
        Executa uma consulta Scatter-Gather em todos os shards em paralelo
        (simulado) e agrega os resultados na aplicação.
        Evita a necessidade de JOINs impossíveis entre shards físicos.
        """
        results = []
        for shard_id, storage in self.shards.items():
            # Simula consulta local em cada shard
            shard_results = [val for val in storage.values() if filter_fn(val)]
            results.extend(shard_results)
        return results


# --- DEMONSTRAÇÃO E TESTES ---

def run_experiment():
    print("=== INICIANDO EXPERIMENTO DE SHARDING NA APLICAÇÃO ===")
    
    # 1. Inicialização com 3 Shards
    shards = ["shard_1", "shard_2", "shard_3"]
    db = ShardedDatabaseClient(shards)
    
    # Inserindo 1000 registros de usuários sintéticos
    print("\n1. Inserindo 1000 usuários nos 3 shards iniciais...")
    for i in range(1000):
        user_id = f"user_{i:04d}"
        user_data = {"id": user_id, "name": f"User {i}", "age": 20 + (i % 40)}
        db.put(user_id, user_data)
        
    # Exibindo a distribuição inicial
    for s_id in shards:
        print(f"   - {s_id}: {len(db.shards[s_id])} registros")

    # 2. Demonstração do Equívoco Comum: Modulo Hash vs Consistent Hashing
    # Se usássemos hash(key) % N, ao mudar de 3 para 4 shards, aproximadamente 75% das chaves mudariam!
    # Vamos calcular quantas chaves mudam de shard com Consistent Hashing:
    temp_ring_3 = ConsistentHashRing()
    for s in ["shard_1", "shard_2", "shard_3"]:
        temp_ring_3.add_node(s)
        
    temp_ring_4 = ConsistentHashRing()
    for s in ["shard_1", "shard_2", "shard_3", "shard_4"]:
        temp_ring_4.add_node(s)
        
    moved_keys = 0
    for i in range(1000):
        key = f"user_{i:04d}"
        if temp_ring_3.get_node(key) != temp_ring_4.get_node(key):
            moved_keys += 1
            
    print(f"\n2. Análise de Impacto de Rebalanceamento:")
    print(f"   - Com Modulo Hash (hash % N): ~750 chaves (75%) mudariam de nó!")
    print(f"   - Com Consistent Hashing: {moved_keys} chaves ({moved_keys/10:.1f}%) mudaram de nó!")
    assert moved_keys < 350, "Consistent Hashing deveria mover apenas cerca de 25% das chaves!"

    # 3. Adição de Shard Online (Sem Downtime)
    # Vamos adicionar o shard_4
    db.add_shard_online("shard_4")
    
    # Testando disponibilidade DURANTE a migração (Lazy Migration ativa)
    print("\n3. Testando leituras durante a migração (Lazy Migration)...")
    all_accessible = True
    for i in range(1000):
        key = f"user_{i:04d}"
        val = db.get(key)
        if val is None:
            all_accessible = False
            break
            
    print(f"   - Todas as chaves continuam acessíveis durante a migração? {all_accessible}")
    assert all_accessible, "Erro: Chaves ficaram inacessíveis durante a migração!"

    # Finaliza a migração ativamente
    db.complete_migration()
    
    # Exibindo a nova distribuição de dados
    print("\n4. Distribuição após a migração completa:")
    for s_id in db.shards:
        print(f"   - {s_id}: {len(db.shards[s_id])} registros")
        
    # Garante que nenhum dado foi perdido
    total_records = sum(len(storage) for storage in db.shards.values())
    print(f"   - Total de registros após rebalanceamento: {total_records}")
    assert total_records == 1000, f"Erro: Esperava 1000 registros, mas encontrou {total_records}!"

    # 5. Consulta Multi-Shard (Scatter-Gather)
    # Vamos buscar todos os usuários com idade igual a 25 anos
    print("\n5. Executando consulta Scatter-Gather (idade == 25)...")
    results = db.scatter_gather_query(lambda user: user["age"] == 25)
    print(f"   - Encontrados {len(results)} usuários com 25 anos.")
    assert len(results) > 0, "Deveria encontrar usuários com 25 anos!"
    
    print("\n=== EXPERIMENTO CONCLUÍDO COM SUCESSO! ===")

if __name__ == "__main__":
    run_experiment()