import functools
import tracemalloc
import logging
import io
import re
import sys

# Configuração do Logger para captura de teste
log_capture_string = io.StringIO()
logger = logging.getLogger("MemoryProfiler")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(log_capture_string)
formatter = logging.Formatter('%(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def profile_memory(func):
    """
    Decorator que registra o pico de memória utilizado durante a execução da função.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Garante que o pico de memória seja resetado para medir apenas esta chamada
        tracemalloc.reset_peak()
        
        result = func(*args, **kwargs)
        
        # Captura o uso atual e o pico
        _, peak = tracemalloc.get_traced_memory()
        
        # Conversão para MB (1024 * 1024)
        peak_mb = peak / (1024 ** 2)
        
        logger.info(f"Peak memory for {func.__name__}: {peak_mb:.2f} MB")
        return result
    return wrapper

def test_mission():
    print("--- Iniciando Testes de Missão ---")
    tracemalloc.start()
    
    # 1. Teste de Integridade de Retorno e Metadados
    @profile_memory
    def allocate_bytes(size_mb):
        """Aloca um bytearray de tamanho específico."""
        return bytearray(size_mb * 1024 * 1024)

    target_size_mb = 5
    expected_bytes = target_size_mb * 1024 * 1024
    
    print(f"Executando alocação de {target_size_mb} MB...")
    result = allocate_bytes(target_size_mb)
    
    # Verificação de Retorno
    assert len(result) == expected_bytes, "ERRO: O retorno da função foi alterado!"
    print("✅ Retorno da função preservado.")
    
    # Verificação de Metadados (Ataque ao equívoco comum de esquecer functools.wraps)
    assert allocate_bytes.__name__ == "allocate_bytes", f"ERRO: Metadados perdidos! Nome: {allocate_bytes.__name__}"
    print("✅ Metadados da função preservados.")

    # 2. Teste de Precisão de Memória (Critério de Sucesso)
    # Pegamos o log gerado
    log_output = log_capture_string.getvalue()
    print(f"Log capturado: {log_output.strip()}")
    
    # Extração do valor numérico via Regex
    match = re.search(r"Peak memory for allocate_bytes: ([\d.]+) MB", log_output)
    if not match:
        raise AssertionError("ERRO: Não foi possível encontrar o log de memória no formato esperado.")
    
    logged_peak_mb = float(match.group(1))
    reference_mb = expected_bytes / (1024 ** 2)
    
    # Cálculo do erro percentual
    error_percent = abs(logged_peak_mb - reference_mb) / reference_mb
    print(f"Valor de referência: {reference_mb:.2f} MB")
    print(f"Valor logado: {logged_peak_mb:.2f} MB")
    print(f"Erro percentual: {error_percent:.2%}")

    # Validação do critério de 10%
    assert error_percent <= 0.10, f"ERRO: O erro de memória ({error_percent:.2%}) excedeu 10%!"
    print("✅ Precisão de memória validada (dentro de 10%).")

    # 3. Teste de Equívoco Comum: Falha sem reset_peak()
    # Se não usássemos reset_peak(), uma função subsequente menor reportaria o pico da maior.
    @profile_memory
    def small_allocation():
        return bytearray(1 * 1024 * 1024)

    print("Executando alocação pequena para testar isolamento...")
    small_allocation()
    log_output_small = log_capture_string.getvalue()
    match_small = re.search(r"Peak memory for small_allocation: ([\d.]+) MB", log_output_small)
    small_peak_mb = float(match_small.group(1))
    
    assert small_peak_mb < 2.0, f"ERRO: O pico da função pequena foi contaminado pelo pico anterior! ({small_peak_mb} MB)"
    print("✅ Isolamento de medição (reset_peak) validado.")

    print("\n--- TODOS OS TESTES PASSARAM COM SUCESSO ---")

if __name__ == "__main__":
    try:
        test_mission()
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        sys.exit(1)