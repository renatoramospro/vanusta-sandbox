import functools
import logging
import tracemalloc
import unittest

# Configuração do logger para capturar as saídas de perfil
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemoryProfiler")

def trace_memory(func):
    """Decorador que registra e loga o pico de memória de uma função."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        try:
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            peak_mb = peak / (1024 * 1024)
            logger.info(f"Função '{func.__name__}' - Pico de memória: {peak_mb:.2f} MB")
            # Armazenamos o pico no wrapper para inspeção programática nos testes
            wrapper.last_peak_bytes = peak
            return result
        finally:
            tracemalloc.stop()
    return wrapper

# Função de teste que aloca exatamente 5 MB (5 * 1024 * 1024 bytes)
@trace_memory
def allocate_five_megabytes():
    # Aloca um bloco de bytes de 5 MB
    data = b'x' * (5 * 1024 * 1024)
    return len(data)

class TestMemoryProfilerDecorator(unittest.TestCase):
    
    def test_return_value_and_side_effects(self):
        """Garante que o decorador não altera o valor de retorno nem a assinatura."""
        self.assertEqual(allocate_five_megabytes.__name__, 'allocate_five_megabytes')
        ret_val = allocate_five_megabytes()
        self.assertEqual(ret_val, 5 * 1024 * 1024)

    def test_peak_memory_within_tolerance(self):
        """Verifica se o pico medido está dentro de 10% da referência de 5 MB."""
        allocate_five_megabytes()
        peak_bytes = getattr(allocate_five_megabytes, 'last_peak_bytes', 0)
        
        expected_bytes = 5 * 1024 * 1024
        # Tolerância de 10%
        lower_bound = expected_bytes * 0.90
        upper_bound = expected_bytes * 1.10
        
        print(f"\n[DIAGNÓSTICO] Esperado: {expected_bytes} bytes | Medido: {peak_bytes} bytes")
        
        self.assertTrue(
            lower_bound <= peak_bytes <= upper_bound,
            f"Pico de memória {peak_bytes} bytes fora da tolerância de 10% (esperado ~{expected_bytes} bytes)."
        )

    def test_common_pitfall_missing_wraps(self):
        """Demonstra o equívoco comum de não usar functools.wraps (contraexemplo)."""
        def bad_decorator(f):
            def inner(*args, **kwargs):
                return f(*args, **kwargs)
            return inner

        @bad_decorator
        def sample_func():
            """Docstring original."""
            pass

        # O equívoco comum faz com que o nome e a docstring se percam
        self.assertNotEqual(sample_func.__name__, 'sample_func') # Na verdade vira 'inner'
        self.assertNotEqual(sample_func.__doc__, 'Docstring original.')

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)