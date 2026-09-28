import time
import sys

class VirtualDatabaseStorage:
    def __init__(self):
        # Simula o armazenamento físico em blocos/páginas (ex: 1000 páginas de dados de produção)
        self.physical_blocks = {f"page_{i}": f"prod_data_{i}" for i in range(1000)}

class DatabaseVirtualClone:
    def __init__(self, parent_storage, max_private_blocks_limit=500):
        start_time = time.time()
        self.parent = parent_storage
        
        # Metadados de Copy-on-Write e controle de ciclo de vida
        self.private_blocks = {}
        self.deleted_pages = set()
        self.max_private_blocks_limit = max_private_blocks_limit # Mitigação de Write Amplification / Esgotamento de Disco
        
        elapsed = time.time() - start_time
        if elapsed > 60.0:
            raise RuntimeError(f"Provisioning took {elapsed}s, exceeding the 60s limit!")
        print(f"[SUCCESS] Virtual clone provisioned in {elapsed:.6f} seconds.")

    def read(self, page_id):
        # 1. Verifica se a página foi explicitamente deletada neste branch (Tombstone)
        if page_id in self.deleted_pages:
            return None
        
        # 2. Verifica se a página foi modificada localmente (espaço privado)
        if page_id in self.private_blocks:
            return self.private_blocks[page_id]
        
        # 3. Suporte a Branching Multinível: Delega a leitura para o pai recursivamente (seja storage ou outro clone)
        return self.parent.read(page_id)

    def write(self, page_id, new_value):
        # Proteção contra Write Amplification descontrolada / Esgotamento de Disco
        if len(self.private_blocks) >= self.max_private_blocks_limit:
            raise RuntimeError(
                f"[CRITICAL ERROR] Storage limit reached for clone! "
                f"Write amplification budget ({self.max_private_blocks_limit} blocks) exhausted."
            )
        
        # Se a página estava marcada como deletada, restauramos/sobrescrevemos com novo valor
        if page_id in self.deleted_pages:
            self.deleted_pages.remove(page_id)

        # Copy-on-Write: Armazena apenas no espaço privado
        if page_id not in self.private_blocks:
            self.private_blocks[page_id] = new_value

    delete(self, page_id):
    def delete(self, page_id):
        # Marcação de deleção lógica (Tombstone) para evitar que o dado reapareça do pai
        self.deleted_pages.add(page_id)
        # Se existia no espaço privado, removemos para liberar metadados locais
        if page_id in self.private_blocks:
            del self.private_blocks[page_id]

def run_test():
    print("--- Iniciando Experimento Avançado de Database Virtual Cloning ---")
    prod_db = VirtualDatabaseStorage()
    print(f"Storage de Produção criado com {len(prod_db.physical_blocks)} páginas.")

    # 1. Criação do Clone Nível 1 (Staging)
    print("\n--- Cenário 1: Criando Clone Nível 1 (Staging) ---")
    staging_clone = DatabaseVirtualClone(prod_db)
    
    # Testa deleção (Tombstone)
    print("Deletando 'page_10' no Staging...")
    staging_clone.delete("page_10")
    assert staging_clone.read("page_10") is None, "Erro: Dado deletado reapareceu no clone!"
    assert prod_db.physical_blocks["page_10"] == "prod_data_10", "Erro: Produção foi afetada pela deleção no clone!"
    print("Sucesso: Deleção isolada corretamente no clone sem afetar a produção.")

    # 2. Criação do Clone Multinível Nível 2 (Clone de Clone - ex: Feature Branch de Dev)
    print("\n--- Cenário 2: Criando Clone Multinível (Clone de Staging) ---")
    dev_clone = DatabaseVirtualClone(staging_clone)
    
    # O Dev lê uma página herdada do Staging que foi deletada lá -> deve retornar None
    assert dev_clone.read("page_10") is None, "Erro: Branch multinível falhou em herdar o estado de deleção do pai!"
    
    # O Dev modifica uma página original do pai do pai
    dev_clone.write("page_20", "dev_modified_data_20")
    assert dev_clone.read("page_20") == "dev_modified_data_20", "Erro na leitura do clone multinível!"
    assert staging_clone.read("page_20") == "prod_data_20", "Erro: Staging foi afetado pelo clone multinível!"
    print("Sucesso: Branching multinível e isolamento validados.")

    # 3. Mitigação de Write Amplification / Esgotamento de Disco
    print("\n--- Cenário 3: Validação de Limite de Storage (Write Amplification) ---")
    small_clone = DatabaseVirtualClone(prod_db, max_private_blocks_limit=2)
    small_clone.write("page_1", "val_1")
    small_clone.write("page_2", "val_2")
    
    try:
        small_clone.write("page_3", "val_3")
        raise AssertionError("Deveria ter bloqueado por limite de storage!")
    except RuntimeError as e:
        print(f"Capturado com sucesso o bloqueio de segurança: {e}")

    print("\Todos os cenários avançados executados e validados com sucesso!")

if __name__ == "__main__":
    try:
        run_test()
        sys.exit(0)
    except AssertionError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)