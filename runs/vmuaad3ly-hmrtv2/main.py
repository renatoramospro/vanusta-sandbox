def decimo(n):
    """Retorna a décima parte de n."""
    return n / 10

# Prova com assert (se o valor estiver incorreto, o programa interrompe aqui)
assert decimo(100) == 10.0
assert decimo(0) == 0.0
assert decimo(-50) == -5.0
assert decimo(5) == 0.5

# Prova com print do resultado
valor_teste = 50
print(f"A décima parte de {valor_teste} é: {decimo(valor_teste)}")