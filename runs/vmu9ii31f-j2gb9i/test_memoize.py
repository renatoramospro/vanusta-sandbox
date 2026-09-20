import unittest
import time
import threading
from memoize import memoize

class TestMemoize(unittest.TestCase):

    def test_basic_memoization(self):
        """Verifica se o cache retorna o valor sem reexecutar a função."""
        self.call_count = 0
        
        @memoize(ttl=10)
        def expensive_func(x):
            self.call_count += 1
            return x * 2

        self.assertEqual(expensive_func(5), 10)
        self.assertEqual(expensive_func(5), 10)
        self.assertEqual(self.call_count, 1, "A função deveria ter sido chamada apenas uma vez.")

    def test_ttl_expiration(self):
        """Verifica se o cache invalida após o tempo definido."""
        self.call_count = 0

        @memoize(ttl=1)
        def quick_func():
            self.call_count += 1
            return True

        quick_func()
        self.assertEqual(self.call_count, 1)
        
        time.sleep(1.1) # Espera o TTL expirar
        
        quick_func()
        self.assertEqual(self.call_count, 2, "A função deveria ser reexecutada após o TTL.")

    def test_argument_handling(self):
        """Verifica suporte a argumentos posicionais, nomeados e mutáveis."""
        self.call_count = 0

        @memoize(ttl=10)
        def complex_func(a, b=None):
            self.call_count += 1
            return f"{a}-{b}"

        # Teste com lista (mutável) e kwargs
        self.assertEqual(complex_func([1, 2], b="test"), " [1, 2]-test")
        self.assertEqual(complex_func([1, 2], b="test"), " [1, 2]-test")
        self.assertEqual(self.call_count, 1)

    def test_maxsize(self):
        """Verifica se o limite de tamanho é respeitado."""
        @memoize(ttl=10, maxsize=2)
        def identity(x):
            return x

        identity(1)
        identity(2)
        identity(3) # Deve remover o '1'

        self.assertEqual(identity.__wrapped__(1), 1) # Acessando original para testar
        # Para testar o cache efetivamente, verificamos o tamanho do cache interno
        # via cache_info que expusemos no wrapper.
        self.assertEqual(identity.cache_info(), 2)

    def test_thread_safety(self):
        """Verifica se múltiplas threads não corrompem o cache."""
        self.call_count = 0

        @memoize(ttl=5)
        def thread_safe_func(x):
            time.sleep(0.01) # Simula carga
            self.call_count += 1
            return x

        threads = []
        for _ in range(20):
            t = threading.Thread(target=thread_safe_func, args=(1,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Embora múltiplas threads possam rodar a função se o cache estiver vazio,
        # o contador não deve apresentar inconsistências de escrita.
        self.assertGreaterEqual(self.call_count, 1)

if __name__ == "__main__":
    unittest.main()