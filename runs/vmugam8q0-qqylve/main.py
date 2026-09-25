import unittest

class TestOAuth2PKCE(unittest.TestCase):
    def test_gerar_code_verifier(self):
        code_verifier = gerar_code_verifier()
        self.assertIsNotNone(code_verifier)

    def test_gerar_code_challenge(self):
        code_verifier = gerar_code_verifier()
        code_challenge = gerar_code_challenge(code_verifier)
        self.assertIsNotNone(code_challenge)

    def test_fazer_requisicao_autorizacao(self):
        code_challenge = gerar_code_challenge(gerar_code_verifier())
        resposta = fazer_requisicao_autorizacao(code_challenge, "S256")
        self.assertIsNotNone(resposta)

    def test_verificar_code_verifier(self):
        code_verifier = gerar_code_verifier()
        code_challenge = gerar_code_challenge(code_verifier)
        self.assertTrue(verificar_code_verifier(code_verifier, code_challenge))

    def test_tratar_erro(self):
        code_verifier = gerar_code_verifier()
        code_challenge = gerar_code_challenge(code_verifier)
        self.assertEqual(tratar_erro(code_verifier, code_challenge), "token")

if __name__ == "__main__":
    unittest.main()