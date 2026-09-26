import sys

def compress(text: str) -> list[int]:
    """Comprime uma string usando o algoritmo LZW e retorna uma lista de inteiros."""
    # Inicializa o dicionário com os 256 caracteres ASCII básicos
    dict_size = 256
    dictionary = {chr(i): i for i in range(dict_size)}
    
    w = ""
    result = []
    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            # Adiciona wc ao dicionário
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
            
    if w:
        result.append(dictionary[w])
    return result

def decompress(compressed: list[int]) -> str:
    """Descomprime uma lista de inteiros codificada em LZW de volta para string."""
    if not compressed:
        return ""
        
    # Inicializa o dicionário reverso
    dict_size = 256
    dictionary = {i: chr(i) for i in range(dict_size)}
    
    w = chr(compressed[0])
    result = [w]
    
    for k in compressed[1:]:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + w[0]
        else:
            raise ValueError(f"Código LZW corrompido ou desconhecido: {k}")
            
        result.append(entry)
        
        # Adiciona w + entry[0] ao dicionário
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        
        w = entry
        
    return "".join(result)

def test_lzw_pipeline():
    print("Iniciando testes do compressor/descompressor LZW...")
    
    # Texto de teste com alta redundância para demonstrar alta taxa de compressão
    sample_text = (
        "A programação de computadores é a arte de dizer ao computador "
        "exatamente o que fazer passo a passo. O algoritmo LZW (Lempel-Ziv-Welch) "
        "é um algoritmo universal de compressão de dados sem perdas criado por "
        "Abraham Lempel, Jacob Ziv e Terry Welch. "
        "Repetição para testar o ganho de compressão: "
        "programação de computadores, programação de computadores, "
        "algoritmo LZW, algoritmo LZW, compressão de dados, compressão de dados. "
        "Caracteres especiais e acentuação: áéíóú ç ãõ Ç ÃÕ 🚀.\n"
    ) * 5
    
    original_bytes = sample_text.encode('utf-8')
    original_size = len(original_bytes)
    
    # Executa compressão
    compressed_codes = compress(sample_text)
    
    # Cada código pode ser representado como inteiro. Para medir o tamanho comprimido de forma justa,
    # calculamos quantos bytes seriam necessários (ex: usando 2 bytes por código se dict_size < 65536).
    max_code = max(compressed_codes) if compressed_codes else 255
    bytes_per_code = 2 if max_code < 65536 else 3
    compressed_size = len(compressed_codes) * bytes_per_code
    
    reduction_pct = (1 - (compressed_size / original_size)) * 100
    
    print(f"Tamanho original: {original_size} bytes")
    print(f"Tamanho comprimido estimado: {compressed_size} bytes ({bytes_per_code} bytes/código)")
    print(f"Taxa de redução de tamanho: {reduction_pct:.2f}%")
    
    assert reduction_pct >= 30, f"Falha no critério de sucesso: redução de {reduction_pct:.2f}% é menor que 30%."
    print("-> Critério de redução de tamanho atingido com sucesso (> 30%)!")
    
    # Executa descompressão
    decompressed_text = decompress(compressed_codes)
    decompressed_bytes = decompressed_text.encode('utf-8')
    
    # Validação bit-perfect
    assert original_bytes == decompressed_bytes, "Erro: O texto descomprimido difere do original!"
    print("-> Recuperação bit-perfect validada com sucesso (0 perdas)!")
    
    # Demonstração do contraexemplo (Equívoco / Corrupção de dados)
    print("\nTestando contraexemplo de corrupção (alteração de código LZW)...")
    corrupted_codes = list(compressed_codes)
    if len(corrupted_codes > 10):
        corrupted_codes[10] = 999999 # Código inválido que não existe no dicionário
        try:
            decompress(corrupted_codes)
        except ValueError as e:
            print(f"-> Contraexemplo capturado com sucesso: {e}")

if __name__ == "__main__":
    test_lzw_pipeline()
    print("\nTudo executado com sucesso e sem erros.")