def inverte_palavras(frase):
    # split() divide a string em uma lista de palavras (removendo espaços extras)
    # [::-1] inverte a ordem dos elementos da lista
    # " ".join() une os elementos da lista em uma string separada por espaços
    return " ".join(frase.split()[::-1])

# Provas de funcionamento com asserts
assert inverte_palavras("olá mundo") == "mundo olá"
assert inverte_palavras("Python é muito legal") == "legal muito é Python"

# Print do resultado solicitado
print(inverte_palavras("O motor da Vanusta está operando"))