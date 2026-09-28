import time
import sys

class VirtualDatabaseStorage:
    def __init__(self):
        # Simula o armazenamento físico em blocos/páginas (ex: 1000 páginas de dados de produção)
        self.physical_blocks = {f"page_{i}": f"prod_data_{i}" for i in range(1000)}
        self.generation = 0

    def get_storage_size_mb(self):
        # Cada página tem 1MB por simplicidade
        return len(self.physical_blocks) * 1.0

class DatabaseVirtualClone:
    def __init__(self, parent_storage: VirtualDatabaseStorage):
        start_time = time.time()
        self.parent = parent_storage
        # O clone virtual armazena apenas um dicionário de metadados/ponteiros para as páginas do pai.
        # Nenhuma cópia física de dados é realizada (Zero Physical Duplication).
        self.clone_pointers = {page_id: "parent" for page_id in parent_storage.physical_blocks.keys()}
        self.private_blocks = {}
        
        elapsed = time.time() - start_time
        if elapsed > 60.0:
            raise RuntimeError(f"Provisioning took {elapsed}s, exceeding the 60s limit!")
        print(f"[SUCCESS] Virtual clone provisioned in {elapsed:.6f} seconds.")

    def read(self, page_id):
        # Leitura lê do bloco privado se modificado, senão lê do pai (COW transparente)
        if page_id in self.private_blocks:
            return self.private_blocks[page_id]
        return self.parent.physical_blocks[page_id]

    def write(self, page_id, new_value):
        # Copy-on-Write: Se o bloco for modificado, criamos a cópia apenas deste bloco no espaço privado do clone.
        # O armazenamento físico global permanece inalterado para as demais páginas.
        if page_id not in self.private_blocks:
            self.private_blocks[page_id] = new_value
            self.clone_pointers[page_id] = "private"

def run_test():
    print("--- Iniciando Experimento de Database Virtual Cloning (COW) ---")
    
    # 1. Produção com grande volume de dados
    prod_db = VirtualDatabaseStorage()
    initial_prod_size = prod_db.get_storage_size_mb()
    print(f"Tamanho do Storage de Produção: {initial_prod_size} MB")

    # 2. Criar Clone Virtual para Testes/Staging
    print("\nCriando Clone Virtual...")
    clone = DatabaseVirtualClone(prod_db)
    
    # 3. Validar se o armazenamento físico duplicou
    # O clone deve apontar para o pai, logo o consumo físico adicional deve ser zero.
    clone_extra_storage = len(clone.private_blocks) * 1.0
    print(fromUtf8 := f"Armazenamento adicional físico usado pelo clone: {clone_extra_storage} MB")
    
    assert clone_extra_storage == 0, "Erro: O clone duplicou o armazenamento físico na criação!"

    # 4. Simular escrita (Copy-on-Write em ação)
    print("\nModificando a página 'page_50' no ambiente de clone...")
    clone.write("page_50", "staging_modified_data_50")
    
    # Verificar que o dado foi alterado no clone mas continua intacto na produção
    assert clone.read("page_50") == "staging_modified_data_50", "Erro na leitura do clone!"
    assert prod_db.physical_blocks["page_50"] == "prod_data_50", "Erro: Produção foi afetada pelo clone!"

    new_clone_storage = len(clone.private_blocks) * 1.0
    print(f"Armazenamento físico adicional após modificar 1 página: {new_clone_storage} MB")
    print("Zero impacto na produção e isolamento de dados validado com sucesso!")

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