import heapq
import json
from collections import Counter

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    # Necessário para o heapq comparar nós com a mesma frequência
    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(frequencies):
    heap = [Node(char, freq) for char, freq in frequencies.items()]
    heapq.heapify(heap)

    if len(heap) == 1:
        # Caso especial para texto com apenas um caractere único
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

def generate_codes(node, current_code="", codes={}):
    if node is None:
        return

    if node.char is not None:
        codes[node.char] = current_code
        return

    generate_codes(node.left, current_code + "0", codes)
    generate_codes(node.right, current_code + "1", codes)
    return codes

def compress(text):
    if not text:
        return "", {}
    
    freqs = Counter(text)
    root = build_huffman_tree(freqs)
    codes = generate_codes(root, "", {})

    encoded_bits = "".join(codes[char] for char in text)
    
    # Preenchimento (padding) para completar múltiplos de 8 bits para gerar bytes
    extra_padding = 8 - (len(encoded_bits) % 8)
    encoded_bits += "0" * extra_padding
    
    byte_array = bytearray()
    for i in range(0, len(encoded_bits), 8):
        byte = encoded_bits[i:i+8]
        byte_array.append(int(byte, 2))

    return bytes(byte_array), freqs, extra_padding

def decompress(byte_array, freqs, extra_padding):
    if not freqs:
        return ""

    root = build_huffman_tree(freqs)
    
    # Reconstrói a string de bits
    bits = "".join(format(byte, '08b') for byte in byte_array)
    if extra_padding > 0:
        bits = bits[:-extra_padding]

    # Decodifica os bits usando a árvore de Huffman
    current_node = root
    decoded_chars = []

    for bit in bits:
        if bit == '0':
            current_node = current_node.left
        else:
            current_node = current_node.right

        if current_node.char is not None:
            decoded_chars.append(current_node.char)
            current_node = root

    return "".join(decoded_chars)

# --- EXPERIMENTO CONCRETO E OBSERVÁVEL ---
if __name__ == "__main__":
    # Texto de teste com redundância estatística significativa (simulando dados reais repetitivos)
    original_text = (
        "O algoritmo de Huffman e um metodo de compressao de dados sem perdas "
        "desenvolvido por David Huffman. A ideia principal e atribuir codigos de "
        "comprimento variavel aos caracteres baseados na sua frequencia de ocorrencia. "
        "Caracteres mais frequentes recebem codigos mais curtos, enquanto caracteres "
        "menos frequentes recebem codigos mais longos. "
    ) * 3

    print(f"Tamanho original do texto: {len(original_text)} caracteres ({len(original_text.encode('utf-8'))} bytes)")

    # 1. Compressão
    compressed_bytes, freqs, padding = compress(original_text)
    
    # O tamanho comprimido total precisa incluir o armazenamento da tabela de frequências (metadados)
    metadata = json.dumps({"freqs": freqs, "padding": padding}).encode('utf-8')
    total_compressed_size = len(compressed_bytes) + len(metadata)

    print(f"Tamanho dos dados comprimidos: {len(compressed_bytes)} bytes")
    print(f"Tamanho dos metadados (tabela de frequências): {len(metadata)} bytes")
    print(f"Tamanho total comprimido (dados + metadados): {total_compressed_size} bytes")

    reduction_percentage = (1 - (total_compressed_size / len(original_text.encode('utf-8')))) * 100
    print(f"Taxa de redução de tamanho: {reduction_percentage:.2f}%")

    # Validação do critério de sucesso (> 30% de redução)
    assert reduction_percentage >= 30, f"Falha: Redução de {reduction_percentage:.2f}% menor que 30%!"
    print("-> Critério de sucesso de redução de tamanho atingido com sucesso!")

    # 2. Descompressão
    restored_text = decompress(compressed_bytes, freqs, padding)

    # Validação lossless (restauração idêntica)
    assert restored_text == original_text, "Falha: O texto restaurado difere do original!"
    print("-> Restauração lossless (idêntica) validada com sucesso!")

    # 3. Contraexemplo: Demonstração de que a árvore NÃO é estática
    text_alternativo = "ABC" * 100
    compressed_alt, freqs_alt, _ = compress(text_alternativo)
    alt_root = build_huffman_tree(freqs_alt)
    alt_codes = generate_codes(alt_root, "", {})
    print(f"Códigos dinâmicos gerados para texto alternativo (A, B, C): {alt_codes}")
    assert len(alt_codes) == 3, "A árvore deve se adaptar dinamicamente aos caracteres presentes."
    print("-> Contraexemplo verificado: Árvore de Huffman é estática/universal? Falso. É totalmente dinâmica e dependente do texto.")