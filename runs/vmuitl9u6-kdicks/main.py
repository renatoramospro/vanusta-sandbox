import hashlib
import unittest

# --- NÍVEL 1 & 2: Rolling Hash O(1) (Adler-32 modificado do Rsync) ---
class RollingChecksum:
    """
    Implementação do hash fraco rolling (Adler-32 modificado) em O(1).
    Fórmula do Rsync: A + B * 2^16 (mod M), onde M = 65536.
    """
    def __init__(self, block_size):
        self.block_size = block_size
        self.MOD = 65536
        self.a = 0
        self.b = 0
        self.window = bytearray()

    def reset(self, data: bytes):
        self.window = bytearray(data)
        self.a = 0
        self.b = 0
        for i, byte in enumerate(data):
            self.a = (self.a + byte) % self.MOD
            self.b = (self.b + (len(data) - i) * byte) % self.MOD

    def roll(self, out_byte: int, in_byte: int):
        """
        Atualiza o hash deslizante em O(1) ao remover o byte que sai (out_byte)
        e adicionar o byte que entra (in_byte).
        """
        self.a = (self.a - out_byte + in_byte) % self.MOD
        self.b = (self.b - self.block_size * out_byte + self.a) % self.MOD
        # Garantir que a e b fiquem positivos em Python
        self.a = (self.a + self.MOD) % self.MOD
        self.b = (self.b + self.MOD) % self.MOD
        return (self.b << 16) | self.a

    def current(self):
        return (self.b << 16) | self.a


# --- NÍVEL 3 & 4: Geração de Assinatura do Arquivo Base ---
def generate_signature(file_data: bytes, block_size: int):
    """
    Gera a assinatura (checksums) do arquivo base:
    Para cada bloco, calcula o hash fraco (rolling) e o hash forte (SHA-256).
    """
    signature = []
    for i in range(0, len(file_data), block_size):
        block = file_data[i:i + block_size]
        
        hasher = RollingChecksum(len(block))
        hasher.reset(block)
        weak_hash = hasher.current()
        strong_hash = hashlib.sha256(block).digest()
        
        signature.append({
            'index': len(signature),
            'weak': weak_hash,
            'strong': strong_hash,
            'size': len(block)
        })
    return signature


# --- NÍVEL 5: Geração de Delta (COPY / LITERAL) ---
def generate_delta(new_file_data: bytes, signature: list, block_size: int):
    """
    Algoritmo de busca gulosa com rolling hash para gerar o delta entre
    o novo arquivo e as assinaturas do arquivo base.
    """
    # Mapeamento de hash fraco para lista de blocos (otimização de busca)
    weak_map = {}
    for entry in signature:
        weak_map.setdefault(entry['weak'], []).append(entry)

    delta = []
    i = 0
    n = len(new_file_data)
    
    # Tratamento para arquivo menor que o block_size
    if n < block_size:
        return [('LITERAL', new_file_data)]

    current_window_size = min(block_size, n)
    hasher = RollingChecksum(current_window_size)
    hasher.reset(new_file_data[0:current_window_size])

    lit_buffer = bytearray()

    while i < n:
        # Se restam menos bytes que o tamanho do bloco, trata o restante como literal
        if i + current_window_size > n:
            lit_buffer.extend(new_file_data[i:])
            break

        weak_h = hasher.current()
        matched = False

        if weak_h in weak_map:
            candidate_block = new_file_data[i:i + current_window_size]
            strong_h = hashlib.sha256(candidate_block).digest()

            for entry in weak_map[weak_h]:
                if entry['strong'] == strong_h:
                    # Match encontrado! Descarrega o buffer literal pendente, se houver
                    if lit_buffer:
                        delta.append(('LITERAL', bytes(lit_buffer)))
                        lit_buffer.clear()

                    delta.append(('COPY', entry['index']))
                    i += current_window_size
                    
                    if i < n:
                        next_window_size = min(block_size, n - i)
                        # Reinicia a janela se o tamanho mudou
                        if next_window_size != current_window_size:
                            current_window_size = next_window_size
                            hasher = RollingChecksum(current_window_size)
                        hasher.reset(new_file_data[i:i + current_window_size])
                    matched = True
                    break

        if not matched:
            # Nenhum match: adiciona o byte atual ao buffer literal e desliza 1 byte
            lit_buffer.append(new_file_data[i])
            i += 1
            if i + current_window_size <= n:
                out_byte = new_file_data[i - 1]
                in_byte = new_file_data[i + current_window_size - 1]
                hasher.roll(out_byte, in_byte)

    if lit_buffer:
        delta.append(('LITERAL', bytes(lit_buffer)))

    return delta


# --- NÍVEL 6: Reconstrução do Arquivo com Validação por Bloco ---
def reconstruct_file(signature: list, delta: list, base_file: bytes):
    """
    Reconstrói o novo arquivo a partir do arquivo base e das instruções do delta,
    validando a integridade forte (SHA-256) de cada bloco copiado.
    """
    reconstructed = bytearray()
    
    # Indexar blocos do arquivo base por índice para acesso O(1)
    base_blocks = {}
    for i, entry in enumerate(signature):
        start = i * entry['size']
        end = start + entry['size']
        base_blocks[entry['index']] = base_file[start:end]

    for instruction, data in delta:
        if instruction == 'LITERAL':
            reconstructed.extend(data)
        elif instruction == 'COPY':
            block_index = data
            block_data = base_blocks[block_index]
            
            # Validação forte por bloco (Segurança solicitada pelo Arquiteto)
            expected_strong = signature[block_index]['strong']
            actual_strong = hashlib.sha256(block_data).digest()
            if actual_strong != expected_strong:
                raise ValueError(f"Corrupção detectada no bloco {block_index}!")
                
            reconstructed.extend(block_data)

    return bytes(reconstructed)


# --- SUÍTE DE TESTES RIGOROSA ---
class TestRsyncAlgorithm(unittest.TestCase):

    def test_edge_case_small_file(self):
        """Testa arquivos menores que o tamanho do bloco."""
        base_file = b"pequeno"
        new_file = b"pequeno modificado"
        signature = generate_signature(base_file, block_size=64)
        delta = generate_delta(new_file, signature, block_size=64)
        reconstructed = reconstruct_file(signature, delta, base_file)
        self.assertEqual(reconstructed, new_file)

    def test_success_criterion_network_reduction(self):
        """
        Critério de Sucesso: Reduzir tráfego de rede em >= 60% para alterações parciais,
        validando integridade final via SHA-256 e por bloco.
        """
        block_size = 64
        # Criar arquivo base de 4096 bytes
        base_file = b"A" * 2048 + b"B" * 2048
        
        # Criar arquivo modificado (alteração parcial pequena no meio)
        new_file = base_file[:2000] + b"X" * 32 + base_file[2032:]

        signature = generate_signature(base_file, block_size)
        delta = generate_delta(new_file, signature, block_size)

        # Calcular tamanho do tráfego do delta (instruções COPY ocupam 8 bytes de metadados, LITERAL o seu tamanho)
        delta_traffic = sum(len(d[1]) if d[0] == 'LITERAL' else 8 for d in delta)
        full_traffic = len(new_file)
        reduction = (1 - (delta_traffic / full_traffic)) * 100

        print(f"\n[Métrica] Tamanho Novo: {full_traffic} bytes")
        print(f"[Métrica] Tráfego Delta: {delta_traffic} bytes")
        print(f"[Métrica] Redução de Tráfego: {reduction:.2f}%")

        # Exigência: Redução >= 60%
        self.assertGreaterEqual(reduction, 60.0)

        # Reconstruir arquivo
        reconstructed = reconstruct_file(signature, delta, base_file)

        # Validação final SHA-256
        self.assertEqual(
            hashlib.sha256(reconstructed).digest(),
            hashlib.sha256(new_file).digest()
        )
        print("[Integridade] SHA-256 final bate perfeitamente com o arquivo esperado!")


if __name__ == '__main__':
    unittest.main()