def balanced_brackets(s):
    stack = []
    mapping = {")": "(", "]": "[", "}": "{"}
    
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping.keys():
            if not stack or stack[-1] != mapping[char]:
                return False
            stack.pop()
            
    return len(stack) == 0

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