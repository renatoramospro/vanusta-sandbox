def is_palindrome(s):
    filtered_s = "".join(char.lower() for char in s if char.isalnum())
    return filtered_s == filtered_s[::-1]

# --- testes do benchmark (não fazem parte da resposta) ---
assert is_palindrome('') is True
assert is_palindrome('A man, a plan, a canal: Panama') is True
assert is_palindrome('Arara') is True
assert is_palindrome('python') is False
assert is_palindrome('12321') is True
assert is_palindrome('ab') is False
print("BENCHMARK_OK")