import time
import sys

class VirtualDatabaseStorage:
    def __init__(self):
        # Simula o armazenamento físico base (produção)
        self.physical_blocks = {f"page_{i}": f"prod_data_{i}" for i in range(1000)}

class DatabaseVirtualClone:
    def __init__(self, parent_storage, max_private_blocks_limit=500):
        start_time = time.time()
        self.parent = parent_storage
        
        # Metadados de Copy-on-Write (COW)
        self.private_blocks = {}
        self.deleted_pages = set()
        self.max_private_blocks_limit = max_private_blocks_limit
        
        elapsed = time.time() - start_time
        if elapsed > 60.0:
            raise RuntimeError(f"Provisioning took {elapsed}s, exceeding the 60s limit!")
        print(f"[SUCCESS] Virtual clone provisioned in {elapsed:.6f} seconds.")

    def read(self, page_id):
        # 1. Verifica se a página foi explicitamente deletada neste branch
        if page_id in self.deleted_pages:
            return None
        
        # 2. Verifica se a página foi modificada localmente (espaço privado)
        if page_id in self.private_blocks:
            return self.private_blocks[page_id]
        
        # 3. Verifica se foi deletada no pai (se o pai for outro clone)
        if hasattr(self.parent, "deleted_pages") and page_id in self.parent.deleted_pages:
            return None

        # 4. Delega a leitura para o pai recursivamente
        if hasattr(self.parent, "read"):
            return self.parent.read(page_id)
        else:
            return self.parent.physical_blocks.get(page_id, None)

    def write(self, page_id, value):
        # Limite de storage privado para mitigar Write Amplification
        total_privates = len(self.private_blocks)
        if page_id not in self.private_blocks and total_privates >= self.max_private_blocks_limit:
            raise RuntimeError(f"Storage limit exceeded! Max private blocks: {self.max_private_blocks_limit}")
        
        # Escrever na página remove eventuais tombstones anteriores (corrige bug de ressurreição/reescrita)
        if page_id in self.deleted_pages:
            self.deleted_pages.remove(page_id)
            
        self.private_blocks[page_id] = value
        print(f"[COW WRITE] Página {page_id} copiada para espaço privado do clone.")

    def delete(self, page_id):
        # Marca a página como deletada (Tombstone) no escopo deste clone
        self.deleted_pages.add(page_id)
        # Se existia no espaço privado local, remove para economizar
        if page_id in self.private_blocks:
            del self.private_blocks[page_id]
        print(f"[TOMBSTONE] Página {page_id} marcada como deletada no clone.")

    def rollback(self):
        # Restaura o branch limpando alterações e tombstones locais
        self.private_blocks.clear()
        self.deleted_pages.clear()
        print("[ROLLBACK] Clone restaurado ao estado inicial do pai.")

def run_test():
    print("--- INICIANDO TESTES DE VIRTUAL CLONING CORRIGIDOS ---")
    
    # 1. Criar storage de produção
    prod_db = VirtualDatabaseStorage()
    
    # 2. Provisionar clone de staging em sub-segundo
    t0 = time.time()
    staging_clone = DatabaseVirtualClone(prod_db, max_private_blocks_limit=10)
    t1 = time.time()
    
    assert (t1 - t0) < 60.0, "Critério de sucesso de tempo falhou!"
    print(f"Tempo de provisionamento: {(t1 - t0)*1000:.2f} ms (Abaixo de 60s)")
    
    # 3. Validar leitura inicial e zero duplicação física
    assert staging_clone.read("page_10") == "prod_data_10"
    print("Leitura inicial validada com sucesso.")
    
    # 4. Testar Escrita COW e Isolamento
    staging_clone.write("page_10", "staging_modified_10")
    assert staging_clone.read("page_10") == "staging_modified_10"
    assert prod_db.physical_blocks["page_10"] == "prod_data_10", "Isolamento de produção quebrou!"
    print("Isolamento de produção validado com sucesso.")

    # 5. Testar Deleção via Tombstone e re-escrita
    staging_clone.delete("page_20")
    assert staging_clone.read("page_20") is None, "Página deletada ressurgiu incorretamente!"
    
    # Re-escrever página deletada (deve ressuscitar com o novo valor)
    staging_clone.write("page_20", "resurrected_data_20")
    assert staging_clone.read("page_20") == "resurrected_data_20", "Falha na re-escrita após deleção!"
    print("Testes de Tombstone e Re-escrita validados com sucesso.")

    # 6. Testar Branching Multinível (Clone de Clone)
    qa_clone = DatabaseVirtualClone(staging_clone)
    assert qa_clone.read("page_10") == "staging_modified_10", "Falha na herança multinível!"
    qa_clone.write("page_10", "qa_modified_10")
    assert qa_clone.read("page_10") == "qa_modified_10"
    assert staging_clone.read("page_10") == "staging_modified_10", "Vazamento entre irmãos/filhos!"
    print("Branching multinível validado com sucesso.")

    # 7. Testar Rollback
    qa_clone.rollback()
    assert qa_clone.read("page_10") == "staging_modified_10", "Rollback falhou em restaurar estado!"
    print("Rollback validado com sucesso.")

    print("\n[SUCCESS] Todos os cenários avançados executados e validados com sucesso!")

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