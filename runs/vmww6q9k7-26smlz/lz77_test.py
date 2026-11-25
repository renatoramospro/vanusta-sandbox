import collections

def find_longest_match(data, window_size):
    """
    Busca a maior repetição de um prefixo de 'data' dentro da janela deslizante.
    Retorna (offset, length) ou (0, 0) se não houver match.
    """
    if not data or window_size <= 0:
        return 0, 0

    # A janela é os 'window_size' bytes ANTES do ponto atual (data)
    # Para simplificar, simulamos a janela como os últimos 'window_size' bytes processados.
    # Em um compressor real, a janela é dinâmica. Aqui, focamos na busca.
    
    # Vamos buscar o prefixo de 'data' (começando do índice 0) na janela.
    # A janela de busca é data[:-1] se estamos processando data[0]
    search_window = data[:-1]
    
    best_match = (0, 0)
    max_len = 0
    
    # Iterar sobre possíveis pontos de início na janela
    for i in range(max(0, len(search_window) - window_size), len(search_window)):
        offset = len(search_window) - i
        
        # Determinar o comprimento máximo possível
        max_possible_len = min(len(data) - i, window_size)
        
        current_len = 0
        # Comparar o prefixo de 'data' com o segmento na janela
        while current_len < max_possible_len and data[current_len] == search_window[i + current_len - offset]:
            current_len += 1
        
        if current_len > max_len:
            max_len = current_len
            best_match = (offset, current_len)
            
    return best_match

# Teste de borda: Repetição clara dentro da janela
# Janela = 10. Dados = "ABCDEFGHIABC"
# O 'ABC' final deve ser encontrado no início.
test_data_repetitivo = b"ABCDEFGHIABC"
window_size = 10
offset, length = find_longest_match(test_data_repetitivo, window_size)

# Teste de borda: Sem repetição
test_data_unico = b"ABCDEFGHIJ"
offset_unico, length_unico = find_longest_match(test_data_unico, window_size)

print(f"Teste Repetitivo (ABCDEFGHIABC, W={window_size}): Offset={offset}, Length={length}")
print(f"Teste Único (ABCDEFGHIJ, W={window_size}): Offset={offset_unico}, Length={length_unico}")

# Verificação de sucesso esperado
assert offset == 10 and length == 3, "Falha no teste de repetição clara."
assert offset_unico == 0 and length_unico == 0, "Falha no teste de dados únicos."