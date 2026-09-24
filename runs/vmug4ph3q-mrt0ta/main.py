def balanced_brackets(s):
    pares = {')': '(', ']': '[', '}': '{'}
    pilha = []

    for caractere in s:
        if caractere in '([{':
            pilha.append(caractere)
        elif caractere in pares:
            if not pilha or pilha.pop() != pares[caractere]:
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