def balanced_brackets(s):
    pilha = []
    mapa = {")": "(", "}": "{", "]": "["}
    for caractere in s:
        if caractere in mapa.values():
            pilha.append(caractere)
        elif caractere in mapa.keys():
            if not pilha or mapa[caractere] != pilha.pop():
                return False
    return not pilha

# --- testes do benchmark (não fazem parte da resposta) ---
assert balanced_brackets('') is True
assert balanced_brackets('()[]{}') is True
assert balanced_brackets('{[()]}') is True
assert balanced_brackets('(]') is False
assert balanced_brackets('([)]') is False
assert balanced_brackets('((') is False
assert balanced_brackets('a(b)c[d]') is True
assert balanced_brackets(')(') is False
print("BENCHMARK_OK")