def dobra(n):
    """Retorna o dobro do número n."""
    return n * 2

# Prova de funcionamento
resultado = dobra(10)

# Assert para validar se o cálculo está correto
assert resultado == 20, f"Erro: Esperava 20, mas obteve {resultado}"

# Print do resultado
print(f"O dobro de 10 é: {resultado}")