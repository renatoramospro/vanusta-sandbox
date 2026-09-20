def decimo(n):
    """Retorna a décima parte de n."""
    return n / 10

if __name__ == "__main__":
    # Definindo um valor para teste
    valor_teste = 100
    resultado = decimo(valor_teste)

    # Prova com assert (se o resultado for diferente de 10.0, o programa lançará um AssertionError)
    assert resultado == 10.0, f"Erro: Esperado 10.0, mas obteve {resultado}"

    # Print do resultado
    print(f"O décimo de {valor_teste} é: {resultado}")