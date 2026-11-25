import unittest
from unittest.mock import patch, Mock
# Importar exceções reais de rede para simulação robusta
import requests.exceptions

# Definir TimeoutError localmente para garantir reprodutibilidade no ambiente de execução
class TimeoutError(Exception):
    """Simulação de TimeoutError para fins de teste."""
    pass

# Simulação de um cliente HTTP que tem um timeout configurado
class ExternalService:
    def __init__(self, timeout=0.1):
        self.timeout = timeout

    # Assinatura que deve ser validada pelo autospec
    def fetch_data(self, endpoint: str) -> dict:
        # Em um cenário real, isso chamaria requests.get(..., timeout=self.timeout)
        raise NotImplementedError("Deve ser mockado para teste")

# Cenário de teste: Simular timeout
class TestIntegrationMocking(unittest.TestCase):
    def test_simula_timeout_com_mock(self):
        # 1. Configurar o mock usando autospec=True para validar o contrato
        # 2. Usar a exceção de timeout esperada (TimeoutError simulado)
        mock_fetch = Mock(side_effect=TimeoutError("Request timed out"))
        
        # 3. Patchar o método fetch_data do serviço, aplicando autospec
        with patch.object(ExternalService, 'fetch_data', autospec=True, return_value=mock_fetch):
            service = ExternalService(timeout=0.1)
            
            # 4. Esperar que a chamada falhe com a exceção específica de timeout
            with self.assertRaises(TimeoutError) as cm:
                service.fetch_data("/data")
            
            # Verificação observável: A exceção correta foi levantada e capturada
            self.assertIn("timed out", str(cm.exception))
            mock_fetch.assert_called_once_with("/data")

    def test_simula_falha_rede_com_mock(self):
        # Cenário de borda: Simular falha de rede (ex: DNS, Conexão)
        mock_fetch = Mock(side_effect=requests.exceptions.ConnectionError("Connection refused"))
        
        with patch.object(ExternalService, 'fetch_data', autospec=True, return_value=mock_fetch):
            service = ExternalService(timeout=0.1)
            
            # Esperar a exceção de conexão real
            with self.assertRaises(requests.exceptions.ConnectionError):
                service.fetch_data("/data")
            
            mock_fetch.assert_called_once_with("/data")


if __name__ == '__main__':
    # Executa o teste e garante que o código de saída seja 0
    unittest.main(argv=['first-arg-is-ignored'], exit=False)