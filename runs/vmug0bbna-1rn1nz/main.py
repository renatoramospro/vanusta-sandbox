def roman_to_int(s: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0

    for i, symbol in enumerate(s):
        value = values[symbol]
        if i + 1 < len(s) and value < values[s[i + 1]]:
            total -= value
        else:
            total += value

    return total

# --- testes do benchmark (não fazem parte da resposta) ---
assert roman_to_int('III') == 3
assert roman_to_int('IV') == 4
assert roman_to_int('IX') == 9
assert roman_to_int('LVIII') == 58
assert roman_to_int('MCMXCIV') == 1994
assert roman_to_int('MMMCMXCIX') == 3999
print("BENCHMARK_OK")