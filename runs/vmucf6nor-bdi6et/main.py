def balanced_brackets(s):
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    opening = set(mapping.values())
    closing = set(mapping.keys())

    for char in s:
        if char in opening:
            stack.append(char)
        elif char in closing:
            if not stack or stack.pop() != mapping[char]:
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