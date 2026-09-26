python path=rsync_prototype.py
import hashlib
import os
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


# --- NÍVEL 3 & 4: G assinatura do arquivo base ---
def generate_signature(file_data: bytes, block_size: int):
    """
    Gera a assinatura (checksums) do arquivo base:
    Para cada bloco, calcula o hash fraco (rolling) e o hash forte (MD5/SHA256).
    """
    signature = []
    for i in range(0, len(file_data), block_size):
        block = file_data[i:i + block_size]
        # Hash fraco inicial
        rc = RollingChecksum(len(block))
        rc.reset(block)
        weak = rc.current()
        # Hash forte para evitar colisões
        strong = hashlib.sha256(block).digest()
        signature.append({
            'index': len(signature),
            'offset': i,
            'length': len(block),
            'weak': weak,
            'strong': strong
        })
    return signature


# --- NÍVEL 5: Algoritmo Delta Encoding (Geração de Instruções) ---
def generate_delta(new_data: bytes, signature: list, block_size: int):
    """
    Compara o novo arquivo com a assinatura do antigo usando busca em tabela hash
    e janela deslizante para gerar instruções COPY(index) ou LITERAL(bytes).
    """
    # Mapear hash fraco para lista de blocos na assinatura
    weak_map = {item['weak']: item for item in signature}
    
    delta = []
    i = 0
    literal_buffer = bytearray()

    while i < len(new_data):
        # Tenta casar usando blocos de tamanho block_size
        match = None
        if i + block_size <= len(new_data):
            candidate_block = new_data[i:i + block_size]
            rc = RollingChecksum(len(candidate_block))
            rc.reset(candidate_block)
            weak_hash = rc.current()

            if weak_hash in weak_map:
                sig_item = weak_map[weak_hash]
                strong_hash = hashlib.sha256(candidate_block).digest()
                if strong_hash == sig_item['strong']:
                    match = sig_item

        if match:
            # Se havia literais acumulados, envia primeiro
            if literal_buffer:
                delta.append(('LITERAL', bytes(literal_buffer)))
                literal_buffer.clear()
            
            delta.append(('COPY', match['index'], match['length']))
            i += match['length']
        else:
            literal_buffer.append(new_data[i])
            i += 1

    if literal_buffer:
        delta.append(('LITERAL', bytes(literal_buffer)))

    return delta


# --- NÍVEL 6: Reconstrução do Arquivo no Receptor ---
def reconstruct_file(signature: list, delta: list, base_data: bytes) -> bytes:
    """
    Reconstrói o novo arquivo a partir do arquivo base e das instruções delta,
    validando a integridade bloco a bloco.
    """
    reconstructed = bytearray()
    
    # Índice de blocos da base para acesso rápido
    blocks_by_index = {}
    for item in signature:
        blocks_by_index[item['index']] = base_data[item['offset']:item['offset'] + item['length']]

    for instr in delta:
        if instr[0] == 'COPY':
            _, idx, length = instr
            block_data = blocks_by_index[idx]
            # Validação de integridade por bloco (previne corrupção intermediária)
            expected_strong = next(item['strong'] for item in signature if item['index'] == idx)
            actual_strong = hashlib.sha256(block_data).digest()
            if actual_strong != expected_strong:
                raise ValueError(f"Corrupção detectada no bloco {idx} durante reconstrução!")
            reconstructed.extend(block_data)
        elif instr[0] == 'LITERAL':
            _, data = instr
            reconstructed.extend(data)

    return bytes(reconstructed)


# --- SUÍTE DE TESTES E VALIDAÇÃO DO CRITÉRIO DE SUCESSO ---
class TestRsyncProtocol(unittest.TestCase):
    
    def test_rolling_hash_o1_behavior(self):
        """Garante que o rolling hash calcula corretamente em O(1)."""
        data = b"Hello, World of Rsync Algorithms!"
        rc = RollingChecksum(8)
        rc.reset(data[0:8])
        h1 = rc.current()
        # Desliza 1 byte
        h2 = rc.roll(data[0], data[8])
        # Recalcula do zero para comparar
        rc_control = RollingChecksum(8)
        rc_control.reset(data[1:9])
        self.assertEqual(h2, rc_control.current())

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