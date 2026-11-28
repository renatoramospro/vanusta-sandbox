def is_palindrome(s):
    processed_s = "".join(filter(str.isalnum, s)).lower()
    return processed_s == processed_s[::-1]

# --- testes do benchmark (não fazem parte da resposta) ---
assert is_palindrome('') is True
assert is_palindrome('A man, a plan, a canal: Panama') is True
assert is_palindrome('Arara') is True
assert is_palindrome('python') is False
assert is_palindrome('12321') is True
assert is_palindrome('ab') is False
print("BENCHMARK_OK")