import hashlib
import bisect
import threading
import time

class ConsistentHashRing:
    """
    Implementação de um anel de Consistent Hashing com nós virtuais.
    Garante distribuição uniforme e evita TypeErrors na busca binária.
    """
    def __init__(self, replicas=32):
        self.replicas = replicas
        self.ring = []  # Lista de tuplas (hash_value, node_name) ordenada
        self.nodes = set()

    def _hash(self, key):
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
        # Correção do bug crítico de TypeError: usamos "" em vez de None
        # para garantir que a comparação de tuplas seja sempre entre strings.
        idx = bisect.bisect_right(self.ring, (val, ""))
        if idx == len(self.ring):
            idx = 0
        return self.ring[idx][1]


class Record:
    """
    Entidade que representa um registro no banco de dados com controle de versão
    para resolução de conflitos em cenários concorrentes.
    """
    def __init__(self, value, version=1):
        self.value = value
        self.version = version

    def __repr__(self):
        return f"Record(value={self.value}, version={self.version})"


class ShardedDatabaseClient:
    """
    Cliente de banco de dados distribuído com suporte a sharding horizontal,
    Consistent Hashing, migração online consistente e Scatter-Gather.
    """
    def __init__(self, initial_shards, replicas=32):
        self.replicas = replicas
        self.ring = ConsistentHashRing(replicas=replicas)
        self.shards = {}
        self.lock = threading.Lock()  # Lock para garantir thread-safety concorrente
        
        # Estado de migração
        self.old_ring = None
        self.migrating = False

        for shard_id in initial_shards:
            self.shards[shard_id] = {}
            self.ring.add_node(shard_id)

    def start_migration(self, new_shard):
        """
        Inicia o processo de migração online de forma segura.
        """
        with self.lock:
            if self.migrating:
                return
            print(f"[SISTEMA] Iniciando migração para adicionar o shard: {new_shard}")
            # Cria uma cópia profunda do anel atual para servir como anel antigo
            self.old_ring = ConsistentHashRing(replicas=self.replicas)
            self.old_ring.ring = list(self.ring.ring)
            self.old_ring.nodes = set(self.ring.nodes)
            
            # Adiciona o novo shard ao anel ativo
            self.shards[new_shard] = {}
            self.ring.add_node(new_shard)
            self.migrating = True

    def put(self, key, value):
        """
        Insere ou atualiza uma chave de forma consistente.
        Se estiver em migração, remove do shard antigo para evitar cópias divergentes.
        """
        with self.lock:
            target_shard = self.ring.get_node(key)
            
            # Se estiver migrando, precisamos evitar cópias divergentes (split-brain local)
            if self.migrating and self.old_ring:
                old_shard = self.old_ring.get_node(key)
                # Se a chave pertencia a outro shard no anel antigo, removemos de lá
                if old_shard != target_shard and key in self.shards[old_shard]:
                    old_record = self.shards[old_shard].pop(key)
                    new_version = old_record.version + 1
                else:
                    new_version = 1
            else:
                # Se já existe, incrementa a versão
                existing = self.shards[target_shard].get(key)
                new_version = (existing.version + 1) if existing else 1

            self.shards[target_shard][key] = Record(value, version=new_version)

    def get(self, key):
        """
        Busca uma chave. Se estiver em migração e a chave não for encontrada
        no novo shard correspondente, busca no shard antigo e realiza Lazy Migration.
        """
        with self.lock:
            target_shard = self.ring.get_node(key)
            record = self.shards[target_shard].get(key)
            
            if record is not None:
                return record.value

            # Lazy Migration ativa durante a migração
            if self.migrating and self.old_ring:
                old_shard = self.old_ring.get_node(key)
                if old_shard != target_shard:
                    old_record = self.shards[old_shard].get(key)
                    if old_record is not None:
                        # Move o dado para o novo shard de forma atômica
                        self.shards[target_shard][key] = old_record
                        self.shards[old_shard].pop(key, None)
                        return old_record.value
            return None

    def delete(self, key):
        """
        Remove uma chave de forma consistente de todos os shards possíveis durante a migração.
        """
        with self.lock:
            removed = False
            target_shard = self.ring.get_node(key)
            if key in self.shards[target_shard]:
                self.shards[target_shard].pop(key)
                removed = True
                
            if self.migrating and self.old_ring:
                old_shard = self.old_ring.get_node(key)
                if old_shard != target_shard and key in self.shards[old_shard]:
                    self.shards[old_shard].pop(key)
                    removed = True
            return removed

    def complete_migration(self):
        """
        Finaliza a migração ativamente, movendo todas as chaves restantes
        que deveriam estar no novo shard mas ainda não foram migradas via Lazy Migration.
        """
        with self.lock:
            if not self.migrating or not self.old_ring:
                return 0

            moved_count = 0
            # Percorre todos os shards antigos para encontrar chaves que agora pertencem a novos shards
            for old_shard_id in list(self.old_ring.nodes):
                keys_to_move = []
                for key in list(self.shards[old_shard_id].keys()):
                    new_shard_id = self.ring.get_node(key)
                    if new_shard_id != old_shard_id:
                        keys_to_move.append((key, new_shard_id))

                for key, new_shard_id in keys_to_move:
                    record = self.shards[old_shard_id].pop(key)
                    self.shards[new_shard_id][key] = record
                    moved_count += 1

            self.migrating = False
            self.old_ring = None
            print(f"[SISTEMA] Migração concluída! {moved_count} chaves foram movidas ativamente.")
            return moved_count

    def scatter_gather_query(self, filter_fn):
        """
        Executa uma consulta paralela simulada em todos os shards e agrega os resultados.
        """
        with self.lock:
            results = []
            for shard_id, storage in self.shards.items():
                for key, record in storage.items():
                    if filter_fn(record.value):
                        results.append((key, record.value))
            return results


def run_experiment():
    print("=== INICIANDO EXPERIMENTO DE SHARDING CORRIGIDO E CONSISTENTE ===")

    # 1. Inicialização com 3 shards
    db = ShardedDatabaseClient(initial_shards=["shard_1", "shard_2", "shard_3"])
    
    # Inserindo 1000 registros iniciais
    print("\n1. Inserindo 1000 usuários nos 3 shards iniciais...")
    for i in range(1000):
        db.put(f"user_{i:04d}", {"name": f"User {i}", "age": 20 + (i % 10)})

    print("   Distribuição inicial:")
    for s_id in sorted(db.shards.keys()):
        print(f"   - {s_id}: {len(db.shards[s_id])} registros")

    # 2. Teste de Robustez contra TypeError na Busca Binária
    # Vamos simular uma busca onde o hash coincide exatamente ou testar a consistência do anel
    print("\n2. Testando segurança da busca binária contra TypeError...")
    try:
        # Força uma busca com chaves variadas para garantir que nenhuma comparação cause TypeError
        for i in range(500):
            db.ring.get_node(f"test_key_{i}")
        print("   - Busca binária executada com sucesso sem TypeErrors!")
    except TypeError as e:
        print(f"   - ERRO DETECTADO: {e}")
        raise e

    # 3. Início da Migração Online Concorrente
    db.start_migration("shard_4")

    # Vamos simular escritas e leituras concorrentes durante a migração
    print("\n3. Simulando operações concorrentes durante a migração...")
    
    # Cenário A: Atualização de uma chave existente durante a migração
    # "user_0005" originalmente pertence a um dos shards iniciais. Vamos atualizá-lo.
    db.put("user_0005", {"name": "User 5 Atualizado", "age": 30})
    
    # Cenário B: Lazy Migration de uma chave não atualizada
    val_lazy = db.get("user_0010")
    print(f"   - Leitura via Lazy Migration de 'user_0010': {val_lazy}")

    # Cenário C: Exclusão de uma chave durante a migração
    db.delete("user_0020")
    assert db.get("user_0020") is None, "Erro: Chave deletada ainda está acessível!"
    print("   - Exclusão de 'user_0020' realizada com sucesso durante a migração.")

    # 4. Finalização da Migração Ativa
    # Como lemos apenas 1 chave via Lazy Migration, a migração ativa deve mover as chaves restantes
    moved = db.complete_migration()
    print(f"   - Chaves movidas ativamente no rebalanceamento: {moved}")
    assert moved > 0, "Erro: Esperava-se que chaves fossem movidas ativamente!"

    # 5. Verificação de Consistência e Integridade dos Dados
    print("\n5. Verificando integridade dos dados pós-migração...")
    
    # O total de registros deve ser 999 (pois deletamos 1)
    total_records = sum(len(storage) for storage in db.shards.values())
    print(f"   - Total de registros ativos: {total_records}")
    assert total_records == 999, f"Erro: Esperava 999 registros, mas encontrou {total_records}!"

    # Garante que a atualização concorrente de 'user_0005' foi preservada
    updated_user = db.get("user_0005")
    print(f"   - Registro 'user_0005' atualizado: {updated_user}")
    assert updated_user["name"] == "User 5 Atualizado", "Erro: Atualização concorrente foi perdida!"

    # 6. Consulta Scatter-Gather
    print("\n6. Executando consulta Scatter-Gather (idade == 30)...")
    results = db.scatter_gather_query(lambda user: user["age"] == 30)
    print(f"   - Encontrados {len(results)} usuários com 30 anos.")
    assert len(results) > 0, "Deveria encontrar usuários com 30 anos!"

    print("\n=== EXPERIMENTO CONCLUÍDO COM SUCESSO! ===")

if __name__ == "__main__":
    run_experiment()