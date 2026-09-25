import hashlib
import time
import random

def sha256(data: bytes) -> bytes:
    """Função auxiliar de hash criptográfico padrão (SHA-256)."""
    return hashlib.sha256(data).digest()

class MerkleTree:
    def __init__(self, blocks: list[bytes]):
        if not blocks:
            raise ValueError("A árvore de Merkle não pode ser vazia.")
        self.blocks = blocks
        self.leaf_count = len(blocks)
        self.levels = self._build_tree(blocks)
        self.root = self.levels[-1][0]

    def _build_tree(self, blocks: list[bytes]) -> list[list[bytes]]:
        # Separação de domínio: prefixo 0x00 para folhas
        current_level = [sha256(b"\x00" + b) for b in blocks]
        levels = [current_level]

        while len(current_level) > 1:
            next_level = []
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            for i in range(0, len(current_level), 2:
                left = current_level[i]
                right = current_level[i+1]
                # Separação de domínio: prefixo 0x01 para nós internos
                parent_hash = sha256(b"\x01" + left + right)
                next_level.append(parent_hash)
            
            levels.append(next_level)
            current_level = next_level

        return levels

    def get_proof(self, index: int) -> list[tuple[bytes, str]]:
        if index < 0 or index >= self.leaf_count:
            raise IndexError(f"Índice {index} fora dos limites para {self.leaf_count} folhas.")
        
        proof = []
        current_index = index
        
        for level_idx in range(len(self.levels) - 1):
            level = self.levels[level_idx]
            is_right_node = (current_index % 2 == 1)
            sibling_index = current_index - 1 if is_right_node else current_index + 1
            
            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
                position = 'left' if is_right_node else 'right'
                proof.append((sibling_hash, position))
            
            current_index //= 2
            
        return proof

    @staticmethod
    def verify_proof(block: bytes, proof: list[tuple[bytes, str]], root: bytes) -> bool:
        if not root:
            return False
        # Separação de domínio para o bloco avaliado
        current_hash = sha256(b"\x00" + block)
        
        try:
            for sibling_hash, position in proof:
                if position == 'left':
                    current_hash = sha256(b"\x01" + sibling_hash + current_hash)
                elif position == 'right':
                    current_hash = sha256(b"\x01" + current_hash + sibling_hash)
                else:
                    return False
        except (TypeError, ValueError):
            return False
            
        return current_hash == root


if __name__ == "__main__":
    print("=== Iniciando Experimento Aprimorado da Árvore de Merkle ===")
    
    num_blocks = 10000
    print(f"\nGerando {num_blocks} blocos de dados sintéticos...")
    data_blocks = [f"bloco_dado_{i}".encode('utf-8') for i in range(num_blocks)]

    # 1. Medição de tempo de construção O(N)
    start_time = time.time()
    tree = MerkleTree(data_blocks)
    build_elapsed = (time.time() - start_time) * 1000
    print(f"Árvore construída em {build_elapsed:.2f} ms (Complexidade O(N)).")
    print(f"Raiz de Merkle (Hex): {tree.root.hex()[:32]}...")

    # 2. Critério de Sucesso: Validar integridade de TODOS os 10.000 blocos
    print(f"\nValidando integridade e provas de inclusão para todos os {num_blocks} blocos...")
    val_start = time.time()
    for i in range(num_blocks):
        p = tree.get_proof(i)
        assert MerkleTree.verify_proof(data_blocks[i], p, tree.root) == True, f"Falha na validação do bloco {i}"
    val_elapsed = (time.time() - val_start) * 1000
    print(f"Validação de 10.000 blocos concluída com sucesso em {val_elapsed:.2f} ms.")

    # 3. Teste de Prova de Inclusão para índice aleatório e validação de índices malformados
    random_index = random.randint(0, num_blocks - 1)
    target_block = data_blocks[random_index]
    proof = tree.get_proof(random_index)
    
    print(f"\n[Teste de Inclusão Individual] Bloco no índice {random_index} verificado com sucesso.")
    
    # Validação de índice fora do limite original (deve lançar IndexError)
    try:
        tree.get_proof(num_blocks + 50)
        assert False, "Deveria ter lançado IndexError para índice fora do limite."
    except IndexError:
        print("[Segurança] Índice inválido rejeitado corretamente via exceção.")

    # 4. Contraexemplo (Corrupção de Dados e Ataque de Domínio)
    print("\n[Contraexemplo] Simulando corrupção de dados em um bloco...")
    corrupted_block = target_block + b"_adulterado"
    is_valid_corrupted = MerkleTree.verify_proof(corrupted_block, proof, tree.root)
    print(f"Verificação com bloco corrompido retornou: {is_valid_corrupted}")
    assert is_valid_corrupted == False, "Erro crítico: A árvore aceitou um bloco corrompido!"
    print("Sucesso: O mecanismo detectou com precisão a adulteração dos dados.")

    print("\nTodos os testes e validações de segurança executados com êxito!")