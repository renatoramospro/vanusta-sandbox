import unittest

class TestMarcoMVP(unittest.TestCase):
    def test_criterio_latencia(self):
        # Critério: Latência < 60s para 10k registros
        tempo_processamento = 45.5  # Simulação de resultado
        self.assertLess(tempo_processamento, 60, "Falha: Latência acima do limite")

    def test_criterio_integridade(self):
        # Critério: 0% de perda de dados
        registros_enviados = 10000
        registros_recebidos = 9995 # Simulação de erro
        self.assertEqual(registros_enviados, registros_recebidos, "Falha: Perda de dados detectada")

if __name__ == "__main__":
    # Executa os testes e captura o resultado
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMarcoMVP)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        print("\n[Resultado] O marco falhou nos critérios de aceite.")
    else:
        print("\n[Resultado] Marco validado com sucesso.")