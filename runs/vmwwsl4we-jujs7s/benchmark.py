import timeit
import time
import sys

# Código dinâmico simples que será otimizado (ex: cálculo simples dentro de um loop)
CODE_TO_TEST = """
result = 0
for i in range(10000):
    result += (i * 2) % 13
"""

# Configuração do benchmark
N_ITERATIONS = 10000
NUMBER_OF_RUNS = 5  # Média de 5 execuções para estabilizar o tempo

def run_original_interpretation():
    """Executa o código diretamente via exec() para simular a interpretação CPython."""
    # Executa o código em um escopo limpo
    exec(CODE_TO_TEST)

print(f"--- Benchmark de Interpretação Original ({N_ITERATIONS} iterações) ---")
times = []
for _ in range(NUMBER_OF_RUNS):
    start_time = time.perf_counter()
    run_original_interpretation()
    end_time = time.perf_counter()
    times.append(end_time - start_time)

avg_original_time = sum(times) / NUMBER_OF_RUNS
print(f"Tempo médio de execução original: {avg_original_time:.6f} segundos")

# Nota: A otimização estática ainda não foi implementada, este é apenas o baseline.
# O próximo passo será compilar este código para um formato estático (ex: bytecode otimizado ou C)
# e medir o tempo otimizado contra este baseline.