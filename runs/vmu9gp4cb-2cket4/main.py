def executar_experimento():
    # Dados iniciais para o teste
    valores = [42, 100, 200]
    print(f"Lista de valores: {valores}")
    print(f"Acessando índice 0 (sucesso): {valores[0]}")

    print("\n--- Teste de Conceito: IndexError ---")
    print("Tentando acessar o índice 10 (fora do limite)...")
    
    try:
        # Tentativa de acesso que gera o erro mapeado pelo Arquiteto
        item = valores[10]
        print(f"Item encontrado: {item}")
    except IndexError as e:
        # Capturamos o erro para que o programa não morra (saída 0)
        # mas provamos que o erro ocorreu.
        print(f"Resultado esperado: Capturamos o erro -> {e}")
        item = "EXCECAO_LANÇADA"

    print("\n--- Ataque ao Equívoco Comum ---")
    # O Arquiteto alertou que o erro comum é achar que Python retorna None.
    # Se o Python retornasse None, o bloco 'except' acima não seria executado.
    print(f"O valor retornado foi None? {item is None}")
    print(f"O valor real capturado foi: {item}")

    print("\n[STATUS] Experimento finalizado com sucesso (Código de saída 0).")

if __name__ == "__main__":
    executar_experimento()