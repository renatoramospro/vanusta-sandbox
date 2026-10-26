def is_palindrome(s):
    filtrado = [c.lower() for c in s if c.isalnum()]
    return filtrado == filtrado[::-1]

# --- testes do benchmark (não fazem parte da resposta) ---
assert is_palindrome('') is True
assert is_palindrome('A man, a plan, a canal: Panama') is True
assert is_palindrome('Arara') is True
assert is_palindrome('python') is False
assert is_palindrome('12321') is True
assert is_palindrome('ab') is False
print("BENCHMARK_OK")