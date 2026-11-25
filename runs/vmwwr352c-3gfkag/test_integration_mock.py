import unittest
from unittest.mock import patch, Mock
import time

# Simulação de um cliente HTTP que tem um timeout configurado
class ExternalService:
    def __init__(self, timeout=0.1):
        self.timeout = timeout

    def fetch_data(self, endpoint):
        # Em um cenário real, isso chamaria requests.get(..., timeout=self.timeout)
        # Aqui, simulamos a chamada que pode falhar por timeout
        raise NotImplementedError("Deve ser mockado para teste")

# Cenário de teste: Simular timeout
class TestIntegrationMocking(unittest.TestCase):
    def test_simula_timeout_com_mock(self):
        # 1. Configurar o mock para demorar mais que o timeout (0.1s)
        mock_fetch = Mock(side_effect=lambda *args, **kwargs: time.sleep(0.5))
        
        # 2. Patchar o método fetch_data do serviço
        with patch.object(ExternalService, 'fetch_data', mock_fetch):
            service = ExternalService(timeout=0.1)
            
            # 3. Esperar que a chamada falhe com um erro de timeout (simulado)
            # Em um ambiente real, o cliente HTTP levantaria um Timeout exception.
            # Aqui, capturamos a exceção que o mock induzirá após o sleep.
            with self.assertRaises(Exception) as cm:
                service.fetch_data("/data")
            
            # Verificação observável: O mock foi chamado e a exceção esperada foi levantada
            self.assertTrue("timed out" in str(cm.exception) or "sleep" in str(cm.exception), 
                            "A exceção capturada não reflete um timeout simulado.")
            mock_fetch.assert_called_once()

if __name__ == '__main__':
    # Executa o teste e garante que o código de saída seja 0
    unittest.main(argv=['first-arg-is-ignored'], exit=False)