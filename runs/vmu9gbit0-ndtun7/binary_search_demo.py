def binary_search_correct(arr, target):
    """
    Busca binária correta utilizando o invariante de intervalo fechado [low, high].
    Invariante: Se o target existe em arr, ele está em arr[low..high].
    """
    low = 0
    high = len(arr) - 1

    while low <= high:
        # Evita estouro de inteiros em linguagens de baixo nível (boa prática)
        mid = low + (high - low) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1  # Descarta a metade inferior incluindo o mid
        else:
            high = mid - 1  # Descarta a metade superior incluindo o mid

    return -1


def binary_search_off_by_one(arr, target):
    """
    Versão com erros propositais de off-by-one:
    1. Condição de parada usa `low < high`, perdendo o elemento quando low == high.
    2. Atualização incorreta de ponteiros (pode gerar comportamento indesejado).
    """
    low = 0
    high = len(arr)

    # ERRO 1: `low < high` faz com que o último elemento isolado nunca seja testado
    while low < high:
        mid = (low + high) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid  # ERRO 2: Deveria ser mid + 1. Causa loop infinito se não tratado,
            # mas com low < high pode apenas pular incorretamente ou falhar.
            # Para simular o off-by-one clássico de limite superior:
            break  # Interrompe para evitar loop infinito na demonstração
        else:
            high = mid

    return -1


def run_tests():
    # 8 vetores sintéticos cobrindo todos os casos de borda solicitados:
    # 1. Vazio, 2. 1 elemento (presente), 3. 1 elemento (ausente),
    # 4. Duplicatas, 5. Alvo ausente, 6. Pontas, 7. Tamanho par, 8. Tamanho ímpar.
    test_cases = [
        ([], 5, -1),                  # 1. Vetor vazio
        ([10], 10, 0),                # 2. 1 elemento (presente)
        ([10], 5, -1),                # 3. 1 elemento (ausente)
        ([1, 2, 2, 2, 3], 2, 2),      # 4. Duplicatas (retorna qualquer índice válido)
        ([1, 3, 5, 7, 9], 6, -1),     # 5. Alvo ausente no meio
        ([1, 3, 5, 7, 9], 1, 0),      # 6. Alvo na ponta esquerda
        ([1, 3, 5, 7, 9], 9, 4),      # 6. Alvo na ponta direita
        ([2, 4, 6, 8], 8, 3),         # 7. Tamanho par
        ([1, 2, 3, 4, 5], 3, 2),      # 8. Tamanho ímpar
    ]

    print("=== TESTANDO VERSÃO CORRETA ===")
    for i, (arr, target, expected) in enumerate(test_cases):
        result = binary_search_correct(arr, target)
        print(f"Caso {i+1}: arr={arr}, target={target} -> Obtido: {result}, Esperado: {expected}")
        if expected == 2 and target == 2:  # Caso de duplicata, qualquer índice válido de 2 serve
            assert result in [1, 2, 3]
        else:
            assert result == expected

    print("\n=== TESTANDO VERSÃO COM OFF-BY-ONE (Esperado falhar em alguns casos) ===")
    failures = 0
    for i, (arr, target, expected) in enumerate(test_cases):
        try:
            result = binary_search_off_by_one(arr, target)
            print(f"Caso {i+1}: arr={arr}, target={target} -> Obtido: {result}, Esperado: {expected}")
            assert result == expected
        except AssertionError:
            failures += 1
            print(f"-> [FALHA CAPTURADA COM SUCESSO] A versão off-by-one errou o Caso {i+1}!")

    print(f"\nTotal de falhas detectadas na versão incorreta: {failures}")
    assert failures > 0, "A versão off-by-one deveria ter falhado em pelo menos um caso!"
    print("Experimento concluído com sucesso absoluto!")


if __name__ == "__main__":
    run_tests()