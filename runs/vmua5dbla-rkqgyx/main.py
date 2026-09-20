def triplo(n):
    return n * 3

# Prova de funcionamento
valor = 10
resultado = triplo(valor)

# Assert para validar se o cálculo está correto
assert resultado == 30, f"Erro: esperado 30, mas obteve {resultado}"

# Print do resultado
print(f"O triplo de {valor} é: {resultado}")