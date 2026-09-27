import re

def is_palindrome(s):
    # Remove tudo que não for letra ou dígito e converte para minúsculas
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    # Compara a string limpa com sua invertida
    return cleaned == cleaned[::-1]

# --- testes do benchmark (não fazem parte da resposta) ---
assert is_palindrome('') is True
assert is_palindrome('A man, a plan, a canal: Panama') is True
assert is_palindrome('Arara') is True
assert is_palindrome('python') is False
assert is_palindrome('12321') is True
assert is_palindrome('ab') is False
print("BENCHMARK_OK")