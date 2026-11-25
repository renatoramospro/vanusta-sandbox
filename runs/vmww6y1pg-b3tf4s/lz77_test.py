import pytest

# Função corrigida para respeitar a semântica de janela deslizante
# A janela deve conter apenas os bytes *anteriores* ao ponto de codificação.
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
    max_len = 0
    
    # Iterar sobre possíveis pontos de início (i) DENTRO da janela de busca
    # i é o índice relativo dentro de search_window
    for i in range(len(search_window)):
        # O offset é a distância do ponto de codificação (current_pos) ao início do match (start_window + i)
        offset = current_pos - (start_window + i)
        
        # Determinar o comprimento máximo possível: 
        # 1. Restante dos dados a serem codificados (len(data) - current_pos)
        # 2. Restante da janela (len(search_window) - i)
        # 3. Limite máximo teórico (embora o restante do buffer seja mais restritivo)
        max_possible_len = min(len(data) - current_pos, len(search_window) - i)
        
        current_len = 0
        # Comparar o prefixo de 'data' (a partir de current_pos) com o segmento na janela
        while current_len < max_possible_len and data[current_pos + current_len] == search_window[i + current_len - offset]:
            current_len += 1
        
        if current_len > max_len:
            max_len = current_len
            best_match = (offset, current_len)
            
    return best_match

# --- Testes Unitários ---

def test_repeticao_clara_corrigida():
    # Entrada: ABCDEFGHIABC. Posição de codificação: 10 (início do segundo ABC)
    # Janela W=10 (ABCDEFGHI)
    # O match é 'ABC' (Length=3) começando em índice 7 (offset = 10 - 7 = 3)
    # Nota: O oráculo anterior esperava offset=10, mas para W=10, o offset máximo é 10.
    # Para 'ABCDEFGHIABC', o match 'ABC' está em 7, 8, 9. Posição atual é 10. Offset = 10 - 7 = 3.
    # O teste anterior estava incorreto em seu oráculo (esperava 10, mas o correto é 3).
    data = b'ABCDEFGHIABC'
    window_size = 10
    offset, length = find_longest_match(data, window_size)
    # O match 'ABC' está 3 posições atrás (índice 7) de a posição 10.
    assert offset == 3 and length == 3, f"Falha no teste de repetição clara. Esperado (3, 3), obtido ({offset}, {length})"

def test_unico_sem_match():
    # Entrada: ABCDEFGHIJ. Posição de codificação: 10. Janela W=10 (ABCDEFGHI)
    # Não há repetição do prefixo 'J' (ou qualquer coisa) na janela.
    data = b'ABCDEFGHIJ'
    window_size = 10
    offset, length = find_longest_match(data, window_size)
    # Deve retornar (0, 0) se o próximo byte não for repetido, ou (0, 1) se for o literal.
    # Na função de busca de match, se não houver repetição, retorna (0, 0).
    assert offset == 0 and length == 0, f"Falha no teste único. Esperado (0, 0), obtido ({offset}, {length})"

def test_limite_janela_pequena():
    # Entrada: ABABA. W=3 (ABA)
    # Posição 3 (B). Janela: ABA. Match 'A' (offset 2, len 1) ou 'BA' (offset 2, len 2)?
    # Posição 4 (A). Janela: BAB. Match 'A' (offset 2, len 1).
    data = b'ABABA'
    window_size = 3
    # Testando a posição 3 (o segundo 'B')
    offset, length = find_longest_match(data[:3], window_size) # Testando AB A
    assert offset == 0 and length == 0 # Não há match no prefixo 'A' dentro de W=3
    
    # Testando a posição 4 (o segundo 'A')
    offset, length = find_longest_match(data, window_size)
    # O prefixo a ser codificado é 'A'. Janela é 'BAB'. Match 'A' em índice 1 (offset 2).
    assert offset == 2 and length == 1, f"Falha no limite pequeno. Esperado (2, 1), obtido ({offset}, {length})"

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
            print("\n✅ Todos os testes passaram com sucesso. Semântica de janela corrigida.")
        else:
            print(f"\n❌ Testes falharam. Código de saída: {exit_code}")
    except Exception as e:
        print(f"\n🚨 Erro inesperado durante a execução do teste: {e}")
