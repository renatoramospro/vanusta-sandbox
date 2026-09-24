def is_palindrome(s):
    cleaned = "".join(char.lower() for char in s if char.isalnum())
    return cleaned == cleaned[::-1]

# --- testes do benchmark (não fazem parte da resposta) ---
assert is_palindrome('') is True
assert is_palindrome('A man, a plan, a canal: Panama') is True
assert is_palindrome('Arara') is True
assert is_palindrome('python') is False
assert is_palindrome('12321') is True
assert is_palindrome('ab') is False
print("BENCHMARK_OK")