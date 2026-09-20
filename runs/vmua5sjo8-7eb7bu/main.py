def metade(n):
    """Retorna a metade de um número n."""
    return n / 2

# Prova de funcionamento
resultado = metade(10)

# O assert verifica se a condição é verdadeira; se não for, o programa para com um erro.
assert resultado == 5.0

# O print exibe o resultado para conferência visual.
print(f"O resultado de metade(10) é: {resultado}")