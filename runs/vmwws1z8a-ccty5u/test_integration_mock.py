import unittest
from unittest.mock import patch, Mock

# --- Definições Locais para Reprodutibilidade (Evita ModuleNotFoundError) ---
class TimeoutError(Exception):
    """Simulação de TimeoutError."""
    pass

class ConnectionError(Exception):
    """Simulação de falha de conexão de rede."""
    pass

class HTTPError(Exception):
    """Simulação de erro HTTP (ex: 500)."""
    def __init__(self, status_code, message="HTTP Error"):
        super().__init__(message)
        self.status_code = status_code

# Simulação de um cliente HTTP
class ExternalService:
    def __init__(self, timeout=0.1):
        self.timeout = timeout

    # Assinatura que deve ser validada pelo autospec
    def fetch_data(self, endpoint: str) -> dict:
        raise NotImplementedError("Deve ser mockado para teste")

# Cenário de teste: Simular timeout (Caso Comum)
class TestIntegrationMocking(unittest.TestCase):
    def test_simula_timeout_com_mock(self):
        mock_fetch = Mock(side_effect=TimeoutError("Request timed out"))
        
        # Autospec garante que a chamada (endpoint: str) está correta
        with patch.object(ExternalService, 'fetch_data', autospec=True, return_value=mock_fetch):
            service = ExternalService(timeout=0.1)
            
            with self.assertRaises(TimeoutError) as cm:
                service.fetch_data("/data")
            
            self.assertIn("timed out", str(cm.exception))
            mock_fetch.assert_called_once_with("/data")

    # Cenário de borda: Simular falha de rede (ConnectionError)
    def test_simula_falha_rede_com_mock(self):
        mock_fetch = Mock(side_effect=ConnectionError("Connection refused"))
        
        with patch.object(ExternalService, 'fetch_data', autospec=True, return_value=mock_fetch):
            service = ExternalService(timeout=0.1)
            
            with self.assertRaises(ConnectionError):
                service.fetch_data("/data")
            
            mock_fetch.assert_called_once_with("/data")

    # Cenário adversarial: Simular erro de serviço (HTTP 500)
    def test_simula_erro_servico_com_mock(self):
        mock_fetch = Mock(side_effect=HTTPError(500, "Internal Server Error"))
        
        with patch.object(ExternalService, 'fetch_data', autospec=True, return_value=mock_fetch):
            service = ExternalService(timeout=0.1)
            
            with self.assertRaises(HTTPError) as cm:
                service.fetch_data("/data")
            
            self.assertEqual(cm.exception.status_code, 500)
            mock_fetch.assert_called_once_with("/data")

    # Cenário comum: Sucesso
    def test_sucesso_com_mock(self):
        expected_data = {"key": "value"}
        mock_fetch = Mock(return_value=expected_data)
        
        with patch.object(ExternalService, 'fetch_data', autospec=True, return_value=mock_fetch):
            service = ExternalService(timeout=0.1)
            
            result = service.fetch_data("/data")
            
            self.assertEqual(result, expected_data)
            mock_fetch.assert_called_once_with("/data")


if __name__ == '__main__':
    # Executa o teste e garante que o código de saída seja 0
    unittest.main(argv=['first-arg-is-ignored'], exit=False)