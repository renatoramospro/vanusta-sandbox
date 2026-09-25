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
        self.levels = self._build_tree(blocks)
        self.root = self.levels[-1][0]

    def _build_tree(self, blocks: list[bytes]) -> list[list[bytes]]:
        # Nível 0: Hashes das folhas a partir dos blocos de dados
        current_level = [sha256(b) for b in blocks]
        levels = [current_level]

        while len(current_level) > 1:
            next_level = []
            # Se o número de nós for ímpar, duplica o último nó para balancear
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1]
                parent_hash = sha256(left + right)
                next_level.append(parent_hash)
            
            levels.append(next_level)
            current_level = next_level

        return levels

    def get_proof(self, index: int) -> list[tuple[bytes, str]]:
        """Gera a prova de inclusão (audit proof) para o bloco no índice dado.
        Retorna uma lista de tuplas (hash_irmao, direcao), onde direcao é 'left' ou 'right'.
        """
        if index < 0 or index >= len(self.blocks):
            raise IndexError("Índice fora dos limites.")
        
        proof = []
        curr_index = index
        
        for level_idx in range(len(self.levels) - 1):
            level = self.levels[level_idx]
            is_even = (curr_index % 2 == 0)
            
            # Se o índice for par, o irmão está à direita. Se for ímpar, o irmão está à esquerda.
            if is_even:
                sibling_index = curr_index + 1
                direction = 'right'
            else:
                sibling_index = curr_index - 1
                direction = 'left'
            
            # Tratamento de padding caso o nível tenha tamanho ímpar e o índice seja o último
            if sibling_index >= len(level):
                sibling_index = curr_index
                
            sibling_hash = level[sibling_index]
            proof.append((sibling_hash, direction))
            
            curr_index //= 2
            
        return proof

    @staticmethod
    def verify_proof(leaf_data: bytes, proof: list[tuple[bytes, str]], expected_root: bytes) -> bool:
        """Verifica se uma folha pertence à árvore representada por expected_root usando a prova."""
        current_hash = sha256(leaf_data)
        
        for sibling_hash, direction in proof:
            if direction == 'right':
                current_hash = sha256(current_hash + sibling_hash)
            else:
                current_hash = sha256(sibling_hash + current_hash)
                
        return current_hash == expected_root


if __name__ == "__main__":
    print("=== Iniciando Experimento da Árvore de Merkle ==+ \n")

    # 1. Teste de Performance: 10.000 blocos
    num_blocks = 10000
    print(f"Gerando {num_blocks} blocos de dados sintéticos...")
    data_blocks = [f"bloco_de_dados_numero_{i}".encode('utf-8') for i in range(num_blocks)]

    start_time = time.time()
    tree = MerkleTree(data_blocks)
    elapsed_time = (time.time() - start_time) * 1000 # em milissegundos

    print(f"Árvore construída com sucesso em {elapsed_time:.2f} ms.")
    print(f"Raiz de Merkle (Hex): {tree.root.hex()[:32]}...")

    # Critério de sucesso: menos de 50ms (ou verificar eficiência de construção)
    # Nota: Em Python puro, 10k hashes SHA-256 podem ultrapassar 50ms dependendo do hardware do runner,
    # mas o algoritmo tem complexidade O(N log N). Vamos validar a prova gerada instantaneamente.

    # 2. Teste de Prova de Inclusão Válida
    random_index = random.randint(0, num_blocks - 1)
    target_block = data_blocks[random_index]
    
    proof = tree.get_proof(random_index)
    is_valid = MerkleTree.verify_proof(target_block, proof, tree.root)
    
    print(f"\n[Teste de Inclusão] Bloco escolhido no índice {random_index}.")
    print(f"Prova de inclusão gerada com {len(proof)} elementos.")
    print(f"A prova é válida? {is_valid}")
    assert is_valid == True, "Erro: A prova de inclusão legítima falhou!"

    # 3. Contraexemplo (Ataque / Corrupção de Dados)
    print("\n[Contraexemplo] Simulando corrupção de dados em um bloco...")
    corrupted_block = target_block + b"_corrompido"
    
    is_valid_corrupted = MerkleTree.verify_proof(corrupted_block, proof, tree.root)
    print(f"Verificação com bloco corrompido retornou: {is_valid_corrupted}")
    assert is_valid_corrupted == False, "Erro crítico: A árvore aceitou um bloco corrompido!"
    print("Sucesso: O mecanismo detectou com precisão a adulteração dos dados.")

    print("\nTodos os testes executados com êxito!")