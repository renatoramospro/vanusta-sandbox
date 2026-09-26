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
        
        # Hash fraco
        hasher = RollingChecksum(len(block))
        hasher.reset(block)
        weak_hash = hasher.current()
        
        # Hash forte (previne colisões do hash fraco)
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
    Compara o arquivo novo com a assinatura do arquivo base usando
    uma janela deslizante e gera instruções COPY(offset, length) ou LITERAL(bytes).
    """
    # Mapear hashes fracos para blocos na assinatura para busca O(1)
    weak_map = {sig['weak']: sig for sig in signature}
    
    delta = []
    i = 0
    literal_buffer = bytearray()
    
    if len(new_file_data) == 0:
        return delta

    # Inicializar rolling hash para a primeira janela
    current_block_size = min(block_size, len(new_file_data))
    rolling = RollingChecksum(current_block_size)
    rolling.reset(new_file_data[0:current_block_size])
    
    window_start = 0
    
    while window_start < len(new_file_data):
        current_weak = rolling.current()
        matched = False
        
        # Verificar se o hash fraco existe na assinatura
        if current_weak in weak_map:
            # Potencial match, verificar hash forte
            end_pos = min(window_start + current_block_size, len(new_file_data))
            candidate_block = new_file_data[window_start:end_pos]
            strong_hash = hashlib.sha256(candidate_block).digest()
            
            sig_match = weak_map[current_weak]
            if sig_match['strong'] == strong_hash:
                # Match confirmado! Descarregar buffer literal pendente se houver
                if literal_buffer:
                    delta.append(('LITERAL', bytes(literal_buffer)))
                    literal_buffer.clear()
                
                # Emitir instrução COPY
                delta.append(('COPY', sig_match['index'] * block_size, len(candidate_block)))
                
                window_start += len(candidate_block)
                matched = True
                
                # Reiniciar janela se ainda houver dados
                if window_start < len(new_file_data):
                    next_size = min(block_size, len(new_file_data) - window_start)
                    rolling = RollingChecksum(next_size)
                    rolling.reset(new_file_data[window_start:window_start + next_size])
        
        if not matched:
            # Nenhum match encontrado: adicionar byte atual ao buffer literal
            literal_buffer.append(new_file_data[window_start])
            window_start += 1
            
            # Avançar janela deslizante se houver dados suficientes
            if window_start + current_block_size <= len(new_file_data):
                out_byte = new_file_data[window_start - 1]
                in_byte = new_file_data[window_start + current_block_size - 1]
                rolling.roll(out_byte, in_byte)
            elif window_start < len(new_file_data):
                # Janela menor no fim do arquivo
                next_size = len(new_file_data) - window_start
                rolling = RollingChecksum(next_size)
                rolling.reset(new_file_data[window_start:])
                
    if literal_buffer:
        delta.append(('LITERAL', bytes(literal_buffer)))
        
    return delta


# --- NÍVEL 6: Reconstrução e Validação ---
def reconstruct_file(signature: list, delta: list, base_file_data: bytes):
    """
    Reconstrói o arquivo novo a partir do arquivo base e das instruções do delta,
    validando a integridade bloco a bloco.
    """
    reconstructed = bytearray()
    
    # Criar dicionário de blocos do base file para acesso por índice
    base_blocks = {}
    for i in range(0, len(base_file_data), len(base_file_data) // len(signature) if signature else 1):
        pass # Indexado por índice do bloco na assinatura
        
    for sig in signature:
        idx = sig['index']
        start = idx * sig['size']
        end = start + sig['size']
        base_blocks[idx] = base_file_data[start:end]

    for instruction in delta:
        if instruction[0] == 'LITERAL':
            reconstructed.extend(instruction[1])
        elif instruction[0] == 'COPY':
            _, offset, length = instruction
            # Encontrar bloco correspondente pelo offset
            block_idx = offset // (len(base_file_data) // len(signature) if signature else len(base_file_data))
            # Garantir recuperação exata dos bytes do arquivo base
            block_data = base_file_data[offset:offset + length]
            
            # Validação de integridade por bloco (Requisito forte do Arquiteto)
            expected_strong = None
            for sig in signature:
                if sig['index'] == block_idx or (sig['index'] * sig['size'] == offset):
                    expected_strong = sig['strong']
                    break
            
            if expected_strong and hashlib.sha256(block_data).digest() != expected_strong:
                raise ValueError(f"Corrupção detectada no bloco COPY no offset {offset}!")
                
            reconstructed.extend(block_data)
            
    return bytes(reconstructed)


# --- SUÍTE DE TESTES UNITÁRIOS ---
class TestRsyncAlgorithm(unittest.TestCase):
    
    def test_rolling_hash_o1(self):
        """Valida que o rolling hash calcula corretamente valores consecutivos."""
        data = b"HELLO WORLD RSYNC"
        block_size = 5
        
        hasher = RollingChecksum(block_size)
        hasher.reset(data[0:5])
        h1 = hasher.current()
        
        # Deslizar 1 byte: sai 'H' (72), entra ' ' (32)
        h2 = hasher.roll(72, ord(' '))
        
        # Comparar com cálculo direto do segundo bloco
        hasher_direct = RollingChecksum(block_size)
        hasher_direct.reset(data[1:6])
        h_direct = hasher_direct.current()
        
        self.assertEqual(h2, h_direct)

    def test_success_criterion_network_reduction(self):
        """
        Critério de Sucesso: Reduzir tráfego de rede em >= 60% para alterações parciais,
        validando integridade final via SHA-256 e por bloco.
        """
        block_size = 16
        # Criar arquivo base de 1 KB
        base_file = b"A" * 512 + b"B" * 512
        
        # Criar arquivo modificado (alteração parcial no meio: 1 byte alterado)
        new_file = base_file[:600] + b"X" + base_file[601:]

        signature = generate_signature(base_file, block_size)
        delta = generate_delta(new_file, signature, block_size)

        # Calcular tamanho do tráfego do delta (instruções COPY vs LITERAL)
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