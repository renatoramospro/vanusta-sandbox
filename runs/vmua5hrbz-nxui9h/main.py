def quadrado(n):
    """Retorna o quadrado de um número n."""
    return n ** 2

# Teste e prova
resultado = quadrado(5)

# O assert verifica se a condição é verdadeira; se não for, o programa para com um erro.
assert resultado == 25, f"Erro: o resultado deveria ser 25, mas foi {resultado}"

# O print exibe o resultado para conferência visual.
print(f"O quadrado de 5 é: {resultado}")