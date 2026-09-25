import heapq
import struct
from collections import Counter

# Limite de segurança para prevenir DoS por descompressão excessiva (Zip Bomb)
MAX_DECOMPRESSED_SIZE = 10 * 1024 * 1024  # 10 MB

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(frequencies):
    if not frequencies:
        return None
    
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
    data = bytearray()
    data.append(len(freqs))
    for char, freq in freqs.items():
        data.append(char)
        data.extend(struct.pack('>I', freq))
    return bytes(data)

def deserialize_freqs(data):
    """
    Desserializa a tabela de frequências com validações rigorosas de segurança:
    - Verifica se há dados suficientes para ler o cabeçalho.
    - Valida se o tamanho do buffer corresponde ao número de símbolos declarados.
    - Valida se as frequências são válidas (> 0).
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Os dados de entrada devem ser do tipo bytes.")
    
    if len(data) < 1:
        raise ValueError("Dados comprimidos truncados: cabeçalho vazio.")

    num_chars = data[0]
    expected_length = 1 + (num_chars * 5)
    
    if len(data) < expected_length:
        raise ValueError(
            f"Dados corrompidos ou truncados: esperados {expected_length} bytes para metadados, "
            f"mas o buffer contém apenas {len(data)} bytes."
        )

    freqs = {}
    idx = 1
    for _ in range(num_chars):
        char = data[idx]
        freq = struct.unpack('>I', data[idx+1:idx+5])[0]
        if freq <= 0:
            raise ValueError(f"Frequência inválida encontrada para o caractere {char}: {freq}")
        freqs[char] = freq
        idx += 5
        
    return freqs, idx

def compress(text):
    if not isinstance(text, str):
        raise TypeError("O texto de entrada deve ser uma string.")
    
    encoded_text = text.encode('utf-8')
    if len(encoded_text) > MAX_DECOMPRESSED_SIZE:
        raise ValueError("Texto excede o limite máximo permitido para compressão.")

    freqs = Counter(encoded_text)
    root = build_huffman_tree(freqs)
    codes = generate_codes(root)

    bit_string = "".join(codes[byte] for byte in encoded_text)
    
    padding_length = (8 - len(bit_string) % 8) % 8
    bit_string += "0" * padding_length

    byte_array = bytearray()
    byte_array.append(padding_length)
    
    for i in range(0, len(bit_string), 8):
        byte_array.append(int(bit_string[i:i+8], 2))

    freqs_bytes = serialize_freqs(freqs)
    compressed_data = freqs_bytes + bytes(byte_array)
    
    return compressed_data, freqs

def decompress(compressed_data):
    if not isinstance(compressed_data, (bytes, bytearray)):
        raise TypeError("Os dados comprimidos devem ser do tipo bytes.")

    freqs, idx = deserialize_freqs(compressed_data)
    
    if len(compressed_data) <= idx:
        raise ValueError("Dados comprimidos corrompidos: ausência de payload de bits.")

    padding_length = compressed_data[idx]
    byte_payload = compressed_data[idx+1:]

    bit_string = "".join(f"{byte:08b}" for byte in byte_payload)
    if padding_length > 0:
        bit_string = bit_string[:-padding_length]

    root = build_huffman_tree(freqs)
    if not root:
        return ""

    decoded_bytes = bytearray()
    current_node = root

    # Validação do tamanho máximo esperado para prevenir DoS
    total_expected_bytes = sum(freqs.values())
    if total_expected_bytes > MAX_DECOMPRESSED_SIZE:
        raise ValueError("Tamanho descomprimido excede o limite seguro de memória.")

    for bit in bit_string:
        if bit == '0':
            current_node = current_node.left
        else:
            current_node = current_node.right

        if current_node.char is not None:
            decoded_bytes.append(current_node.char)
            current_node = root
            
            # Verificação de segurança em tempo de execução para evitar loops infinitos ou expansão descontrolada
            if len(decoded_bytes) > MAX_DECOMPRESSED_SIZE:
                raise ValueError("Violação de limite de segurança: dados descomprimidos excederam o tamanho esperado.")

    return decoded_bytes.decode('utf-8')

if __name__ == "__main__":
    original_text = (
        "O algoritmo de Huffman é um método clássico e eficiente para compressão de dados "
        "sem perdas (lossless). Ele atribui códigos de comprimento variável aos caracteres "
        "com base na frequência com que eles aparecem no texto de entrada. Caracteres mais "
        "frequentes recebem códigos mais curtos, enquanto caracteres raros recebem códigos mais longos. "
        "Essa estratégia maximiza a eficiência de armazenamento e transmissão, garantindo reduções "
        "significativas no tamanho total do arquivo sem corromper nenhuma informação. "
        "A segurança e robustez do código exigem validação rigorosa de limites de entrada e metadados. "
    ) * 5

    encoded_original = original_text.encode('utf-8')
    original_size = len(encoded_original)
    print(f"Tamanho original do texto: {len(original_text)} caracteres ({original_size} bytes)")

    compressed_data, freqs = compress(original_text)
    total_compressed_size = len(compressed_data)

    print(f"Tamanho total comprimido (metadados otimizados + dados): {total_compressed_size} bytes")

    reduction_percentage = (1 - (total_compressed_size / original_size)) * 100
    print(f"Taxa de redução de tamanho: {reduction_percentage:.2f}%")

    assert reduction_percentage >= 30, f"Falha: Redução de {reduction_percentage:.2f}% menor que 30%!"
    print("-> Critério de sucesso de redução de tamanho (>30%) atingido com sucesso!")

    restored_text = decompress(compressed_data)
    assert restored_text == original_text, "Falha: O texto restaurado difere do original!"
    print("-> Restauração lossless (idêntica) validada com sucesso!")

    # Testes unitários de Segurança e Robustez contra entradas malformadas
    print("-> Executando testes de robustez e segurança contra entradas malformadas...")
    
    # 1. Teste com dados truncados
    try:
        decompress(b'\x05\x41') # Declara 5 caracteres mas fornece apenas 1 byte
        raise AssertionError("Deveria ter falhado com dados truncados!")
    except ValueError as e:
        print(f"   [OK] Capturado com sucesso (Truncamento): {e}")

    # 2. Teste com cabeçalho vazio
    try:
        decompress(b'')
        raise AssertionError("Deveria ter falhado com cabeçalho vazio!")
    except ValueError as e:
        print(f"   [OK] Capturado com sucesso (Cabeçalho Vazio): {e}")

    print("-> Todos os testes de segurança e funcionalidade passaram com sucesso absoluto!")