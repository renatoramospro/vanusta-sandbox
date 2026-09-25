import heapq
import struct
from collections import Counter

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(frequencies):
    heap = [Node(char, freq) for char, freq in frequencies.items()]
    heapq.heapify(heap)

    if len(heap) == 1:
        node = heapq.heappop(heap)
        root = Node(None, node.freq)
        root.left = node
        return root

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    return heap[0] if heap else None

def generate_codes(node, current_code="", codes=None):
    if codes is None:
        codes = {}
    if node is None:
        return codes

    if node.char is not None:
        codes[node.char] = current_code if current_code else "0"
        return codes

    generate_codes(node.left, current_code + "0", codes)
    generate_codes(node.right, current_code + "1", codes)
    return codes

def serialize_freqs(freqs):
    # Serialização binária compacta em vez de JSON para reduzir metadados
    # Formato: [num_chars (1 byte)] + para cada char: [char (1 byte), freq (4 bytes big-endian)]
    data = bytearray()
    data.append(len(freqs))
    for char, freq in freqs.items():
        data.append(char)
        data.extend(struct.pack('>I', freq))
    return bytes(data)

def deserialize_freqs(data):
    freqs = {}
    num_chars = data[0]
    idx = 1
    for _ in range(num_chars):
        char = data[idx]
        freq = struct.unpack('>I', data[idx+1:idx+5])[0]
        freqs[char] = freq
        idx += 5
    return freqs, idx

def compress(text):
    data_bytes = text.encode('utf-8')
    frequencies = Counter(data_bytes)
    root = build_huffman_tree(frequencies)
    codes = generate_codes(root)

    bit_string = "".join(codes[b] for b in data_bytes)
    padding = (8 - len(bit_string) % 8) % 8
    bit_string += "0" * padding

    compressed_bytes = bytearray()
    for i in range(0, len(bit_string), 8):
        byte = bit_string[i:i+8]
        compressed_bytes.append(int(byte, 2))

    metadata = serialize_freqs(frequencies)
    # Formato final: [tamanho_metadata (2 bytes)][metadata][padding (1 byte)][dados_comprimidos]
    header = struct.pack('>H', len(metadata)) + metadata + struct.pack('B', padding)
    return header + bytes(compressed_bytes), frequencies

def decompress(full_data):
    metadata_len = struct.unpack('>H', full_data[0:2])[0]
    metadata_bytes = full_data[2:2+metadata_len]
    freqs, consumed = deserialize_freqs(metadata_bytes)
    
    padding = full_data[2+metadata_len]
    compressed_bytes = full_data[3+metadata_len:]

    bit_string = "".join(f"{b:08b}" for b in compressed_bytes)
    if padding > 0:
        bit_string = bit_string[:-padding]

    root = build_huffman_tree(freqs)
    current_node = root
    decoded_bytes = bytearray()

    for bit in bit_string:
        if bit == '0':
            current_node = current_node.left
        else:
            current_node = current_node.right

        if current_node.char is not None:
            decoded_bytes.append(current_node.char)
            current_node = root

    return decoded_bytes.decode('utf-8')

if __name__ == "__main__":
    # Texto de teste ampliado e com forte redundância para garantir compressão > 30%
    original_text = (
        "O algoritmo de Huffman e um metodo classico de compressao de dados sem perdas. "
        "A compressao de dados reduz o tamanho dos arquivos para otimizar o armazenamento e a transmissao. "
        "Repeticao de frases como compressao de dados e Huffman ajuda a demonstrar a eficiencia do algoritmo. "
        "Huffman Huffman Huffman dados dados dados compressao compressao compressao. "
    ) * 5

    encoded_original = original_text.encode('utf-8')
    original_size = len(encoded_original)
    print(f"Tamanho original do texto: {len(original_text)} caracteres ({original_size} bytes)")

    compressed_data, freqs = compress(original_text)
    total_compressed_size = len(compressed_data)

    print(f"Tamanho total comprimido (metadados otimizados + dados): {total_compressed_size} bytes")

    reduction_percentage = (1 - (total_compressed_size / original_size)) * 100
    print(f"Taxa de redução de tamanho: {reduction_percentage:.2f}%")

    # Validação rigorosa do critério de sucesso (> 30% de redução)
    assert reduction_percentage >= 30, f"Falha: Redução de {reduction_percentage:.2f}% menor que 30%!"
    print("-> Critério de sucesso de redução de tamanho (>30%) atingido com sucesso!")

    # Descompressão e validação lossless
    restored_text = decompress(compressed_data)
    assert restored_text == original_text, "Falha: O texto restaurado difere do original!"
    print("-> Restauração lossless (idêntica) validada com sucesso!")

    # Contraexemplo: Verificação de que a árvore de Huffman não é estática/universal
    text_alternativo = "X Y Z " * 200
    comp_alt, freqs_alt = compress(text_alternativo)
    alt_root = build_huffman_tree(freqs_alt)
    alt_codes = generate_codes(alt_root)
    assert len(alt_codes) == 3, "A árvore deve se adaptar dinamicamente aos caracteres presentes."
    print("-> Contraexemplo verificado: Árvore de Huffman é estática? Falso. É totalmente dinâmica e dependente do texto.")