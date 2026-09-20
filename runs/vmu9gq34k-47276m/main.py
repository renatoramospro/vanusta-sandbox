def executar_experimento():
    # Lista de exemplo conforme o plano original
    valores = [10, 20, 30, 42]
    print(f"antes do erro: resultado parcial {valores[3]}")

    print("testando acesso ao índice 10 (fora do limite)...")

    # O Arquiteto mapeou o equívoco comum: achar que Python retorna None ao acessar índice inválido.
    # Vamos demonstrar que o comportamento real é disparar uma exceção.
    try:
        # Tentativa de acesso que causaria falha fatal se não fosse tratada
        valor_invalido = valores[10]
        
        # Se o código chegar aqui, o comportamento está incorreto (não lançou erro)
        print(f"ERRO DE CONCEITO: O Python retornou {valor_invalido} em vez de lançar IndexError.")
    except IndexError as e:
        # Este é o caminho esperado para validar o conceito técnico
        print(f"Sucesso no teste de conceito: {type(e).__name__} foi disparado corretamente.")
        print(f"Mensagem do erro: {e}")

    print("Experimento concluído com sucesso.")

if __name__ == "__main__":
    executar_experimento()