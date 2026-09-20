def cubo(n):
    """Retorna o número n elevado ao cubo."""
    return n ** 3

# Prova com assert e print
resultado = cubo(3)
assert resultado == 27, f"Erro: esperado 27, obtido {resultado}"

print(f"O resultado de 3 ao cubo é: {resultado}")