def fizzbuzz_list(n):
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append('FizzBuzz')
        elif i % 3 == 0:
            result.append('Fizz')
        elif i % 5 == 0:
            result.append('Buzz')
        else:
            result.append(str(i))
    return result

# --- testes do benchmark (não fazem parte da resposta) ---
assert fizzbuzz_list(0) == []
assert fizzbuzz_list(5) == ['1', '2', 'Fizz', '4', 'Buzz']
assert fizzbuzz_list(15)[-1] == 'FizzBuzz'
assert fizzbuzz_list(15)[9] == 'Buzz' and fizzbuzz_list(15)[11] == 'Fizz'
assert len(fizzbuzz_list(100)) == 100
print("BENCHMARK_OK")