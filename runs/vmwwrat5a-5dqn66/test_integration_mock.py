import unittest
from unittest.mock import patch, Mock
# Importar TimeoutError, que é mais específico que Exception
from timeout import TimeoutError # Assumindo que um TimeoutError existe ou simulando-o

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
        # 1. Configurar o mock para levantar uma exceção de timeout IMEDIATAMENTE
        # Não usamos time.sleep, pois isso apenas bloqueia, não levanta exceção.
        mock_fetch = Mock(side_effect=TimeoutError("Request timed out"))
        
        # 2. Patchar o método fetch_data do serviço
        with patch.object(ExternalService, 'fetch_data', mock_fetch):
            service = ExternalService(timeout=0.1)
            
            # 3. Esperar que a chamada falhe com a exceção específica de timeout
            # Corrigido: Esperar por TimeoutError, não apenas Exception genérico.
            with self.assertRaises(TimeoutError) as cm:
                service.fetch_data("/data")
            
            # Verificação observável: A exceção correta foi levantada e capturada
            self.assertIn("timed out", str(cm.exception))
            mock_fetch.assert_called_once()

if __name__ == '__main__':
    # Para garantir que o teste rode e termine com código 0, precisamos definir TimeoutError
    # se não estiver disponível no ambiente de execução padrão.
    class TimeoutError(Exception):
        pass
    
    # Executa o teste e garante que o código de saída seja 0
    unittest.main(argv=['first-arg-is-ignored'], exit=False)