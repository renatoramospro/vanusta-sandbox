def balanced_brackets(s):
    stack = []
    bracket_pairs = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in bracket_pairs.values():
            stack.append(char)
        elif char in bracket_pairs:
            if not stack or stack.pop() != bracket_pairs[char]:
                return False
    return not stack

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