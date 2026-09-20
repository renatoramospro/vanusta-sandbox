def conta_vogais(texto):
    # Inclui vogais padrão e variações acentuadas comuns no português
    vogais = "aeiouAEIOUáéíóúÁÉÍÓÚâêîôûÂÊÎÔÛãõÃÕàèìòùÀÈÌÒÙ"
    return sum(1 for char in texto if char in vogais)

# Provas com asserts
assert conta_vogais("Python") == 1
assert conta_vogais("Ritm") == 0

# Print do resultado
print(f"Resultado para 'Olá, Lua!': {conta_vogais('Olá, Lua!')}")