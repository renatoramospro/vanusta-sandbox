import sys

# Limites de segurança para evitar ataques de negação de serviço (DoS)
MAX_DICT_SIZE = 65536     # Limita o crescimento do dicionário para evitar consumo excessivo de memória
MAX_DECOMPRESSED_SIZE = 10 * 1024 * 1024  # Limite máximo de 10 MB na descompressão (proteção contra Zip Bomb)

def compress(data: bytes) -> list[int]:
    """
    Comprime uma sequência de bytes usando o algoritmo LZW (Lempel-Ziv-Welch).
    Inclui proteção contra entradas vazias e teto de crescimento do dicionário (DoS).
    """
    if not data:
        return []
    
    # Inicializa o dicionário com todos os valores de bytes individuais (0 a 255)
    dictionary = {bytes([i]): i for i in range(256)}
    dict_size = 256
    
    w = b""
    result = []
    
    for byte in data:
        kb = bytes([byte])
        wk = w + kb
        if wk in dictionary:
            w = wk
        else:
            result.append(dictionary[w])
            # Só adiciona ao dicionário se não atingir o limite máximo de segurança
            if dict_size < MAX_DICT_SIZE:
                dictionary[wk] = dict_size
                dict_size += 1
            w = kb
            
    if w:
        result.append(dictionary[w])
        
    return result

def decompress(compressed: list[int]) -> bytes:
    """
    Descomprime uma lista de códigos LZW de volta para a sequência de bytes original.
    Inclui validações rigorosas de códigos inválidos e limites de tamanho (segurança anti-DoS).
    """
    if not compressed:
        return b""
        
    # Validação inicial de tipo e estrutura
    if not isinstance(compressed, list):
        raise TypeError("A entrada comprimida deve ser uma lista de inteiros.")

    # Inicializa o dicionário reverso
    dictionary = {i: bytes([i]) for i in range(256)}
    dict_size = 256
    
    # Valida o primeiro código
    first_code = compressed[0]
    if first_code not in dictionary:
        raise ValueError(f"Código LZW inicial inválido ou corrompido: {first_code}")
        
    w = dictionary[first_code]
    result = [w]
    total_size = len(w)
    
    for k in compressed[1:]:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + w[:1]
        else:
            raise ValueError(f"Código LZW inválido ou corrompido: {k}")
            
        result.append(entry)
        total_size += len(entry)
        
        # Proteção contra estouro de memória (Zip Bomb / Denial of Service)
        if total_size > MAX_DECOMPRESSED_SIZE:
            raise ValueError("Tamanho descomprimido excede o limite seguro permitido (Zip Bomb detectada).")
            
        # Adiciona ao dicionário respeitando o teto de segurança
        if dict_size < MAX_DICT_SIZE:
            dictionary[dict_size] = w + entry[:1]
            dict_size += 1
            
        w = entry
        
    return b"".join(result)

def test_lzw_pipeline():
    print("Iniciando testes de segurança e robustez do compressor/descompressor LZW...")
    
    # 1. Teste com entrada vazia (borda)
    assert compress(b"") == []
    assert decompress([]) == b""
    print("-> Teste de entrada vazia validado com sucesso!")

    # 2. Teste com texto Unicode e Emojis
    sample_text = "Olá, Mundo! 🚀 LZW algorithm em Python 3. 🐍" * 100
    original_bytes = sample_text.encode('utf-8')
    original_size = len(original_bytes)
    
    compressed_codes = compress(original_bytes)
    
    # Estimativa de tamanho comprimido com base em 2 bytes por código (abaixo de MAX_DICT_SIZE)
    bytes_per_code = 2
    compressed_size = len(compressed_codes) * bytes_per_code
    reduction_pct = (1 - (compressed_size / original_size)) * 100
    
    print(f"Tamanho original: {original_size} bytes")
    print(f"Tamanho comprimido estimado: {compressed_size} bytes")
    print(f"Taxa de redução de tamanho: {reduction_pct:.2f}%")
    
    # Recuperação bit-perfect
    decompressed_bytes = decompress(compressed_codes)
    assert original_bytes == decompressed_bytes, "Erro: O conteúdo descomprimido difere do original!"
    print("-> Recuperação bit-perfect validada com sucesso!")

    # 3. Teste de contraexemplo de corrupção / código inválido
    print("Testando contraexemplo de corrupção...")
    corrupted_codes = list(compressed_codes)
    if len(corrupted_codes) > 10:
        corrupted_codes[10] = 999999  # Código fora do dicionário
        try:
            decompress(corrupted_codes)
            raise AssertionError("Deveria ter falhado com ValueError!")
        except ValueError as e:
            print(f"-> Contraexemplo capturado com segurança: {e}")

    # 4. Teste de proteção contra Zip Bomb / limite de memória
    print("Testando proteção contra Zip Bomb (lista excessiva de códigos)...ate")
    malicious_bomb = [65] * (MAX_DECOMPRESSED_SIZE + 1)
    try:
        decompress(malicious_bomb)
        raise AssertionError("Deveria ter bloqueado por limite de tamanho!")
    except ValueError as e:
        print(f"-> Proteção anti-DoS / Zip Bomb acionada com sucesso: {e}")

if __name__ == "__main__":
    test_lzw_pipeline()
    print("\nTudo executado com sucesso e com total segurança aplicada.")