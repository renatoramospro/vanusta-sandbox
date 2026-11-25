import pytest
import sys

# Função corrigida para respeitar a semântica de janela deslizante
def find_longest_match(data, window_size):
    """
    Busca a maior repetição de um prefixo de 'data' (a partir do índice 0) 
    dentro da janela deslizante definida pelos 'window_size' bytes anteriores.
    Retorna (offset, length) ou (0, 0) se não houver match.
    """
    if not data or window_size <= 0:
        return 0, 0

    # Posição atual (onde estamos codificando) é len(data)
    current_pos = len(data)
    
    # A janela de busca é o segmento de dados de tamanho 'window_size' 
    # terminando imediatamente antes de current_pos.
    start_window = max(0, current_pos - window_size)
    search_window = data[start_window:current_pos]
    
    best_match = (0, 0)
    
    # Iterar sobre possíveis pontos de início (i) DENTRO da janela de busca
    # i é o índice relativo dentro de search_window
    for i in range(len(search_window)):
        # O offset é a distância do ponto de codificação (current_pos) ao início do match (start_window + i)
        offset = current_pos - (start_window + i)
        
        current_len = 0
        # Loop de comparação byte a byte
        while (current_pos + current_len < len(data) and 
               i + current_len < len(search_window) and
               data[current_pos + current_len] == search_window[i + current_len]):
            current_len += 1
        
        # Atualizar o melhor match encontrado
        if current_len > best_match[1]:
            best_match = (offset, current_len)
            
    return best_match

def test_repeticao_clara_corrigida():
    # Entrada: ABCDEFGHIABC. Posição de codificação: 10 (início do segundo ABC)
    # Janela W=10 (ABCDEFGHI)
    # O match é 'ABC' (Length=3) começando em índice 7 (offset = 10 - 7 = 3)
    data = b'ABCDEFGHIABC'
    window_size = 10
    offset, length = find_longest_match(data, window_size)
    assert offset == 3 and length == 3, f"Falha no teste de repetição clara. Esperado (3, 3), obtido ({offset}, {length})"

def test_limite_janela_pequena():
    # Entrada: ABABA. W=3. Testando posição 4 (o segundo 'A').
    # Posição 4. Janela: BAB (start_window=1). Prefixo: A.
    # Match 'A' em índice 1 da janela (offset = 4 - (1+1) = 2). Length=1.
    data = b'ABABA'
    window_size = 3
    offset, length = find_longest_match(data, window_size)
    assert offset == 2 and length == 1, f"Falha no limite pequeno. Esperado (2, 1), obtido ({offset}, {length})"

def test_unico_sem_match():
    data = b'ABCDEFGHIJ'
    window_size = 10
    offset, length = find_longest_match(data, window_size)
    assert offset == 0 and length == 0, f"Falha no teste único. Esperado (0, 0), obtido ({offset}, {length})"

def test_limite_janela_zero():
    data = b'ABC'
    window_size = 0
    offset, length = find_longest_match(data, window_size)
    assert offset == 0 and length == 0

# Execução para demonstrar o resultado observável
if __name__ == "__main__":
    # Executa os testes e imprime o resultado de forma observável
    print("--- Executando Testes LZ77 Corrigidos ---")
    try:
        # Usamos pytest.main() para garantir que a saída seja clara e o código 0
        exit_code = pytest.main([__file__])
        if exit_code == 0:
            print("\n✅ Todos os testes passaram com sucesso. Semântica de janela e aritmética de índice corrigidas.")
        else:
            print(f"\n❌ Testes falharam. Código de saída: {exit_code}")
    except Exception as e:
        print(f"\n🚨 Erro inesperado durante a execução do teste: {e}")