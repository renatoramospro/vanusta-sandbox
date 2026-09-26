import sys

def compress(data: bytes) -> list[int]:
    """
    Comprime uma sequência de bytes usando o algoritmo LZW (Lempel-Ziv-Welch).
    Operar diretamente sobre bytes garante robustez total para qualquer caractere Unicode (UTF-8).
    """
    # Inicializa o dicionário com todos os valores de bytes individuais (0 a 255)
    dictionary = {bytes([i]): i for i in range(256)}
    dict_size = 256
    
    w = b""
    result = []
    
    for byte in data:
        # Cria um objeto bytes de um único elemento para combinar
        kb = bytes([byte])
        wk = w + kb
        if wk in dictionary:
            w = wk
        else:
            result.append(dictionary[w])
            # Adiciona wk ao dicionário se houver espaço (limite prático opcional, aqui dinâmico)
            dictionary[wk] = dict_size
            dict_size += 1
            w = kb
            
    if w:
        result.append(dictionary[w])
        
    return result

def decompress(compressed: list[int]) -> bytes:
    """
    Descomprime uma lista de códigos LZW de volta para a sequência de bytes original.
    """
    # Inicializa o dicionário reverso/direto com bytes individuais
    dictionary = {i: bytes([i]) for i in range(256)}
    dict_size = 256
    
    if not compressed:
        return b""
        
    w = dictionary[compressed[0]]
    result = [w]
    
    for k in compressed[1:]:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + w[0:1]
        else:
            raise ValueError(f"Código LZW inválido ou corrompido: {k}")
            
        result.append(entry)
        
        # Adiciona a nova sequência ao dicionário
        dictionary[dict_size] = w + entry[0:1]
        dict_size += 1
        
        w = entry
        
    return b"".join(result)

def test_lzw_pipeline():
    print("Iniciando testes do compressor/descompressor LZW com suporte a Unicode/Emojis...")
    
    # Texto altamente repetitivo contendo caracteres especiais, acentuação e emojis (🚀)
    sample_text = (
        "O algoritmo LZW (Lempel-Ziv-Welch) é um método de compressão sem perdas "
        "extremamente eficiente para dados repetitivos. 🚀 Testando emojis e caracteres "
        "especiais: ç, ã, ê, à, ö. " * 50
    )
    
    original_bytes = sample_text.encode('utf-8')
    original_size = len(original_bytes)
    
    # Executa compressão
    compressed_codes = compress(original_bytes)
    
    # Estima o tamanho comprimido usando o número de bytes necessários por código
    max_code = max(compressed_codes) if compressed_codes else 255
    bytes_per_code = 2 if max_code < 65536 else 3
    compressed_size = len(compressed_codes) * bytes_per_code
    
    reduction_pct = (1 - (compressed_size / original_size)) * 100
    
    print(f"Tamanho original: {original_size} bytes")
    print(f"Tamanho comprimido estimado: {compressed_size} bytes ({bytes_per_code} bytes/código)")
    print(f"Taxa de redução de tamanho: {reduction_pct:.2f}%")
    
    # Critério de sucesso: redução de pelo menos 30%
    assert reduction_pct >= 30, f"Falha no critério de sucesso: redução de {reduction_pct:.2f}% é menor que 30%."
    print("-> Critério de redução de tamanho atingido com sucesso (> 30%)!")
    
    # Executa descompressão
    decompressed_bytes = decompress(compressed_codes)
    
    # Validação bit-perfect
    assert original_bytes == decompressed_bytes, "Erro: O conteúdo descomprimido difere do original!"
    print("-> Recuperação bit-perfect validada com sucesso (0 perdas)!")
    
    # Demonstração do contraexemplo (corrupção de dados tratada corretamente)
    print("\nTestando contraexemplo de corrupção (alteração de código LZW)...")
    corrupted_codes = list(compressed_codes)
    if len(corrupted_codes) > 10:  # Sintaxe corrigida corretamente
        corrupted_codes[10] = 999999 # Código inválido que não existe no dicionário
        try:
            decompress(corrupted_codes)
        except ValueError as e:
            print(f"-> Contraexemplo capturado com sucesso: {e}")

if __name__ == "__main__":
    test_lzw_pipeline()
    print("\nTudo executado com sucesso e sem erros.")